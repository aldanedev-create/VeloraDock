import { createLandscape } from "./landscape.ts";

export async function createWorld(host: HTMLElement, onDestination: (query: string) => void): Promise<any> {
  // The Three.js runtime is packaged locally and loaded only when the world is enabled.
  const moduleUrl: string = "/assets/vendor/three.module.js";
  const THREE: any = await import(moduleUrl);
  const scene = new THREE.Scene();
  scene.background = new THREE.Color(0xadcfcf);
  scene.fog = new THREE.FogExp2(0xadcfcf, .0018);
  const camera = new THREE.PerspectiveCamera(55, 1, .5, 1800);
  const renderer = new THREE.WebGLRenderer({ antialias: true, powerPreference: "low-power" });
  renderer.setPixelRatio(Math.min(window.devicePixelRatio, 1.25));
  renderer.outputColorSpace = THREE.SRGBColorSpace;
  host.appendChild(renderer.domElement);
  renderer.domElement.setAttribute("aria-label", "Explorable VeloraDock islands. Drag to look, scroll to zoom, use W A S D to move.");
  renderer.domElement.tabIndex = 0;
  scene.add(new THREE.HemisphereLight(0xe6fbff, 0x426257, 2.7));
  const sunlight = new THREE.DirectionalLight(0xfff1c7, 2.5);
  sunlight.position.set(-100, 160, 70);
  scene.add(sunlight);
  const landscape = createLandscape(THREE, scene);
  const target = new THREE.Vector3(0, 6, 0);
  let angle = .35;
  let elevation = .7;
  let distance = 130;
  let active = !document.hidden;
  let paused = window.matchMedia("(prefers-reduced-motion: reduce)").matches;
  let exploring = false;
  let dragging = false;
  let lastX = 0;
  let lastY = 0;
  let moved = false;
  let previous = 0;
  let frame = 0;
  const keys = new Set<string>();
  const reduced = window.matchMedia("(prefers-reduced-motion: reduce)");

  function render() {
    camera.position.set(target.x + Math.sin(angle) * distance * Math.cos(elevation), target.y + Math.sin(elevation) * distance, target.z + Math.cos(angle) * distance * Math.cos(elevation));
    camera.lookAt(target);
    renderer.render(scene, camera);
  }
  function resize() {
    renderer.setSize(host.clientWidth || 1, host.clientHeight || 1, false);
    camera.aspect = (host.clientWidth || 1) / (host.clientHeight || 1);
    camera.updateProjectionMatrix();
    render();
  }
  function animate(now: number) {
    frame = 0;
    if (!active || paused) return;
    frame = requestAnimationFrame(animate);
    if (now - previous < 33) return;
    const delta: number = Math.min((now - previous) / 1000, .06);
    previous = now;
    if (exploring) {
      const speed: number = 60 * delta;
      if (keys.has("w") || keys.has("arrowup")) target.z -= speed;
      if (keys.has("s") || keys.has("arrowdown")) target.z += speed;
      if (keys.has("a") || keys.has("arrowleft")) target.x -= speed;
      if (keys.has("d") || keys.has("arrowright")) target.x += speed;
      target.x = Math.max(-330, Math.min(330, target.x));
      target.z = Math.max(-330, Math.min(330, target.z));
    }
    for (const beacon of landscape.beacons) beacon.rotation.y += delta * .35;
    for (const cloud of landscape.clouds) {
      cloud.position.x += delta * 1.5;
      if (cloud.position.x > 350) cloud.position.x = -350;
    }
    render();
  }
  function pointerDown(event: PointerEvent) {
    if (!exploring) return;
    dragging = true;
    moved = false;
    lastX = event.clientX;
    lastY = event.clientY;
    renderer.domElement.setPointerCapture(event.pointerId);
  }
  function pointerMove(event: PointerEvent) {
    if (!dragging) return;
    const dx: number = event.clientX - lastX;
    const dy: number = event.clientY - lastY;
    if (Math.abs(dx) + Math.abs(dy) > 2) moved = true;
    angle -= dx * .006;
    elevation = Math.max(.15, Math.min(1.25, elevation + dy * .005));
    lastX = event.clientX;
    lastY = event.clientY;
    render();
  }
  function pointerUp(event: PointerEvent) {
    dragging = false;
    if (!exploring || moved) return;
    const bounds = renderer.domElement.getBoundingClientRect();
    const ray = new THREE.Raycaster();
    ray.setFromCamera(new THREE.Vector2((event.clientX - bounds.left) / bounds.width * 2 - 1, -(event.clientY - bounds.top) / bounds.height * 2 + 1), camera);
    const hits = ray.intersectObjects(landscape.beacons);
    if (hits.length) onDestination(hits[0].object.userData.query);
  }
  function wheel(event: WheelEvent) {
    if (!exploring) return;
    event.preventDefault();
    distance = Math.max(35, Math.min(350, distance + event.deltaY * .1));
    render();
  }
  function keyDown(event: KeyboardEvent) {
    if (!exploring || !["w", "a", "s", "d", "arrowup", "arrowdown", "arrowleft", "arrowright"].includes(event.key.toLowerCase())) return;
    event.preventDefault();
    keys.add(event.key.toLowerCase());
    if (paused) {
      const key: string = event.key.toLowerCase();
      target.x += ["a", "arrowleft"].includes(key) ? -4 : ["d", "arrowright"].includes(key) ? 4 : 0;
      target.z += ["w", "arrowup"].includes(key) ? -4 : ["s", "arrowdown"].includes(key) ? 4 : 0;
      render();
    }
  }
  function keyUp(event: KeyboardEvent) { keys.delete(event.key.toLowerCase()); }
  function schedule() { cancelAnimationFrame(frame); frame = 0; previous = performance.now(); if (active && !paused) frame = requestAnimationFrame(animate); }
  function visibility() { active = !document.hidden; schedule(); if (active) render(); }
  function blur() { keys.clear(); dragging = false; }
  function motion() { paused = reduced.matches; schedule(); render(); }
  const observer = new ResizeObserver(resize);
  observer.observe(host);
  renderer.domElement.addEventListener("pointerdown", pointerDown);
  renderer.domElement.addEventListener("pointermove", pointerMove);
  renderer.domElement.addEventListener("pointerup", pointerUp);
  renderer.domElement.addEventListener("pointercancel", blur);
  renderer.domElement.addEventListener("wheel", wheel, { passive: false });
  renderer.domElement.addEventListener("keydown", keyDown);
  renderer.domElement.addEventListener("keyup", keyUp);
  renderer.domElement.addEventListener("blur", blur);
  document.addEventListener("visibilitychange", visibility);
  reduced.addEventListener("change", motion);
  resize();
  schedule();
  return {
    pause(value: boolean) { paused = value; schedule(); render(); },
    explore(value: boolean) { exploring = value; keys.clear(); if (value) renderer.domElement.focus(); },
    visible(value: boolean) { active = value && !document.hidden; keys.clear(); schedule(); },
    home() { target.set(0, 6, 0); angle = .35; elevation = .7; distance = 130; render(); },
    travel(index: number) {
      const island = landscape.islands[index];
      if (!island) return;
      target.set(island.x, 6, island.z);
      distance = 100;
      render();
    },
    dispose() {
      cancelAnimationFrame(frame);
      observer.disconnect();
      document.removeEventListener("visibilitychange", visibility);
      reduced.removeEventListener("change", motion);
      scene.traverse((object: any) => {
        object.geometry?.dispose();
        if (object.material) {
          const materials = Array.isArray(object.material) ? object.material : [object.material];
          for (const material of materials) material.dispose();
        }
      });
      renderer.dispose();
      renderer.forceContextLoss();
      renderer.domElement.remove();
    },
  };
}
