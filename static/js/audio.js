'use strict';
// One audio context, bounded decoded-buffer cache, and disposable crossfade voices.
window.WhatIfAudio = (() => {
  const titles = {
    main:'Between Possibilities', orbital:'Distant Habitats', tape:'After the Last Broadcast',
    noir:'An Unfinished Statement', mystery:'Under the Familiar', neon:'Rain on Circuit Glass',
    city:'Windows After Sunset', quantum:'A Second Morning', clock:'The Minute Between',
    wilderness:'Beyond the Shelter', uncanny:'The Room Remembers'
  };
  let context, master, compressor, analyser, current, generation = 0;
  let enabled = false, volume = .35, desired = {profile:'main', seed:'lobby', tension:0};
  let cueKey = '', loading = false;
  const buffers = new Map(), voices = new Set();
  const listeners = new Set();
  const hash = text => [...text].reduce((n,c) => ((n * 31 + c.charCodeAt(0)) >>> 0), 7);
  const status = () => ({enabled, volume, profile:desired.profile, title:titles[desired.profile],
    running:enabled && context?.state === 'running', loading, voices:voices.size, cached:buffers.size, signal:signalLevel()});
  const emit = () => { for (const listener of listeners) listener(status()); };

  function createContext() {
    if (context?.state === 'closed') { context=null; current=null; cueKey=''; buffers.clear(); voices.clear(); }
    if (context) return;
    const Audio = window.AudioContext || window.webkitAudioContext;
    if (!Audio) throw new Error('This browser does not support the soundtrack. You can still play quietly.');
    context = new Audio();
    master = context.createGain(); master.gain.value = volume;
    compressor = context.createDynamicsCompressor();
    compressor.threshold.value = -12; compressor.ratio.value = 4;
    analyser = context.createAnalyser(); analyser.fftSize = 1024;
    master.connect(compressor); compressor.connect(analyser); analyser.connect(context.destination);
    context.onstatechange = emit;
  }

  function signalLevel() {
    if(!analyser)return 0;
    const samples=new Float32Array(analyser.fftSize);analyser.getFloatTimeDomainData(samples);
    return Math.max(...samples.map(Math.abs));
  }

  async function buffer(profile) {
    if (buffers.has(profile)) {
      const item = buffers.get(profile); buffers.delete(profile); buffers.set(profile,item); return item;
    }
    const response = await fetch('/static/audio/' + profile + '.wav');
    if (!response.ok) throw new Error('The soundtrack could not load. Check that the audio folder was extracted.');
    const decoded = await context.decodeAudioData(await response.arrayBuffer());
    buffers.set(profile,decoded);
    while (buffers.size > 3) buffers.delete(buffers.keys().next().value);
    return decoded;
  }

  function retire(voice, fade = .7) {
    if (!voice || voice.retiring) return;
    voice.retiring = true;
    const now = context.currentTime;
    voice.gain.gain.cancelScheduledValues(now);
    voice.gain.gain.setValueAtTime(voice.gain.gain.value, now);
    voice.gain.gain.linearRampToValueAtTime(0, now + fade);
    voice.source.stop(now + fade + .03);
  }

  async function switchTrack(force = false) {
    if (!enabled || !context || document.hidden) return;
    const targetKey = desired.profile + ':' + desired.seed;
    if (!force && cueKey === targetKey && current) {
      current.filter.frequency.setTargetAtTime(2400+desired.tension*4200,context.currentTime,1.2);
      current.gain.gain.setTargetAtTime(.72+desired.tension*.08,context.currentTime,1.2);
      return;
    }
    const token = ++generation;
    const requested = {...desired}; loading = true; emit();
    try {
      const decoded = await buffer(requested.profile);
      if (token !== generation || !enabled || document.hidden) return;
      const source = context.createBufferSource(), gain = context.createGain(), filter = context.createBiquadFilter();
      filter.type='lowpass';filter.Q.value=.35;filter.frequency.value=requested.profile==='main'?6500:2400+requested.tension*4200;
      source.buffer = decoded; source.loop = true;
      source.playbackRate.value = rate(); gain.gain.value = 0;
      source.connect(filter);filter.connect(gain); gain.connect(master);
      const voice = {source,gain,filter,retiring:false}; voices.add(voice);
      source.onended = () => {source.disconnect();filter.disconnect();gain.disconnect();voices.delete(voice);emit();};
      // Every story has a stable variation; all offsets stay inside its genre score.
      const offset = requested.profile === 'main' ? 0 : hash(requested.seed) % Math.max(1,Math.floor(decoded.duration / 2));
      source.start(0, offset); gain.gain.linearRampToValueAtTime(.8, context.currentTime + .75);
      retire(current); current = voice; cueKey = targetKey;
    } catch(error) {
      if(token===generation){pause();throw error;}
    } finally {if(token===generation){loading=false;emit();}}
  }

  function rate() {
    return desired.profile === 'main' ? 1 : .985 + (hash(desired.seed) % 7) / 200;
  }

  async function enable() {
    createContext();
    // Resume is called before the first await while the user gesture is active.
    const resume = context.resume(); enabled = true; emit();
    try {await resume; await switchTrack();}
    catch(error){pause();throw error;}
  }

  function pause() {
    enabled=false; generation++; loading=false; cueKey='';
    for(const voice of voices)retire(voice,.08);
    current=null; emit();
  }

  async function scene(profile='main',seed='lobby',tension=0) {
    desired={profile:Object.hasOwn(titles,profile)?profile:'main',seed:String(seed),tension:Math.max(0,Math.min(1,tension))};
    emit(); await switchTrack();
  }

  function setVolume(value) {
    volume=Math.max(0,Math.min(1,Number(value)||0));
    if(master)master.gain.setTargetAtTime(volume,context.currentTime,.05);
    emit();
  }

  function chime(ending=false) {
    if(!enabled || context?.state!=='running')return;
    const notes=ending?[0,7,12]:[0];
    for(const [i,semitone] of notes.entries()){
      const oscillator=context.createOscillator(), gain=context.createGain();
      const now=context.currentTime+i*.12;
      const roots={main:48,orbital:45,tape:53,noir:43,mystery:50,neon:41,city:55,quantum:48,clock:50,wilderness:43,uncanny:41};
      oscillator.frequency.value=440*2**((roots[desired.profile]+24+semitone-69)/12);
      gain.gain.setValueAtTime(0,now);gain.gain.linearRampToValueAtTime(.055,now+.02);
      gain.gain.exponentialRampToValueAtTime(.001,now+.4);
      oscillator.connect(gain);gain.connect(master);
      oscillator.start(now);oscillator.stop(now+.42);
      oscillator.onended=()=>{oscillator.disconnect();gain.disconnect();};
    }
  }

  document.addEventListener('visibilitychange',async()=>{
    if(!context)return;
    try {
      if(document.hidden){generation++;loading=false;await context.suspend();}
      else if(enabled){await context.resume();await switchTrack();}
    }catch(_){pause();}
    emit();
  });
  window.addEventListener('pagehide',()=>{pause();if(context)context.close();});
  return {enable,pause,scene,setVolume,chime,status,subscribe(listener){listeners.add(listener);listener(status());return()=>listeners.delete(listener);}};
})();
