# Island workspace

`ui/components/WorldScene.html` owns controls and user preferences. `ui/world/scene.ts` manages the camera, input, render lifecycle and disposal. `ui/world/landscape.ts` builds the six islands and their destination beacons.

The renderer is limited to approximately 30 frames per second and a device pixel ratio of 1.25. It stops scheduling frames when paused or hidden. Windows hide/show hooks supplement document visibility. Reduced motion pauses autonomous animation; camera controls remain usable. Disabling releases WebGL resources. Files are never represented or uploaded into the scene.

Three.js r160 is pinned in public/vendor with its MIT license. It is lazy-loaded from the local application server and is separate from the MinifyJS-optimized application bundle. The scene is a decorative, explorable island workspace, rather than a full game.

Before release, test movement, resize, reduced motion, hide/show, disable/re-enable, GPU fallback and native icon behavior on Windows 10/11. Compare idle memory with the world enabled and disabled using tools/measure_windows.py.
