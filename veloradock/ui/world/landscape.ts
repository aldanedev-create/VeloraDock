// Deterministic procedural scenery: no downloaded models or textures.
export function createLandscape(THREE: any, scene: any) {
  const water = new THREE.Mesh(
    new THREE.PlaneGeometry(1600, 1600),
    new THREE.MeshStandardMaterial({ color: 0x1b7888, roughness: 0.36, metalness: 0.22 })
  );
  water.rotation.x = -Math.PI / 2;
  water.position.y = -1;
  scene.add(water);

  const islands = [
    { x: 0, z: 0, radius: 60, label: "Home harbor", query: "" },
    { x: 125, z: -85, radius: 35, label: "Apps island", query: "app " },
    { x: -110, z: -75, radius: 38, label: "Files island", query: "file " },
    { x: 10, z: -190, radius: 32, label: "Actions island", query: "run " },
    { x: -100, z: 110, radius: 29, label: "Clipboard island", query: "clip " },
    { x: 135, z: 105, radius: 34, label: "Numbers island", query: "= " },
  ];
  const beacons: any[] = [];
  const leaves = new THREE.MeshStandardMaterial({ color: 0x3b8b62, flatShading: true });
  const bark = new THREE.MeshStandardMaterial({ color: 0x675747 });

  for (const island of islands) {
    const geometry = new THREE.PlaneGeometry(island.radius * 2.4, island.radius * 2.4, 28, 28);
    geometry.rotateX(-Math.PI / 2);
    const positions = geometry.attributes.position;
    const colors: number[] = [];
    for (let index = 0; index < positions.count; index++) {
      const x: number = positions.getX(index);
      const z: number = positions.getZ(index);
      const distance: number = Math.sqrt(x * x + z * z) / island.radius;
      const ridge: number = Math.max(0, 1 - distance) * 14;
      const noise: number = Math.sin(x * .12) * Math.cos(z * .15) * Math.max(0, 1 - distance) * 4;
      const height: number = distance > 1.05 ? -3 : Math.max(-2, ridge + noise);
      positions.setY(index, height);
      const color = new THREE.Color(height < 2 ? 0xd6c698 : height > 10 ? 0x6b9180 : 0x508e68);
      colors.push(color.r, color.g, color.b);
    }
    geometry.setAttribute("color", new THREE.Float32BufferAttribute(colors, 3));
    geometry.computeVertexNormals();
    const land = new THREE.Mesh(geometry, new THREE.MeshStandardMaterial({ vertexColors: true, flatShading: true }));
    land.position.set(island.x, 0, island.z);
    scene.add(land);

    for (let index = 0; index < 18; index++) {
      const angle: number = index * 2.399;
      const radius: number = island.radius * (.23 + (index % 5) * .08);
      const x: number = Math.cos(angle) * radius;
      const z: number = Math.sin(angle) * radius;
      const height: number = (1 - radius / island.radius) * 14 + Math.sin(x * .12) * Math.cos(z * .15) * (1 - radius / island.radius) * 4;
      const trunk = new THREE.Mesh(new THREE.CylinderGeometry(.4, .7, 4, 5), bark);
      trunk.position.set(island.x + x, height + 2, island.z + z);
      scene.add(trunk);
      const tree = new THREE.Mesh(new THREE.ConeGeometry(3, 7, 6), leaves);
      tree.position.set(island.x + x, height + 6, island.z + z);
      scene.add(tree);
    }

    const beacon = new THREE.Mesh(
      new THREE.OctahedronGeometry(4),
      new THREE.MeshStandardMaterial({ color: 0x83ffe0, emissive: 0x2b8c79, emissiveIntensity: .7 })
    );
    beacon.position.set(island.x, 25, island.z);
    beacon.userData = island;
    scene.add(beacon);
    beacons.push(beacon);
  }
  // Cloud banks and a small harbor give the world a recognizable silhouette.
  const cloudMaterial = new THREE.MeshStandardMaterial({ color: 0xf1f4e7, roughness: 1 });
  const clouds: any[] = [];
  for (let index = 0; index < 16; index++) {
    const cloud = new THREE.Group();
    for (let part = 0; part < 4; part++) {
      const puff = new THREE.Mesh(new THREE.IcosahedronGeometry(7 + part, 1), cloudMaterial);
      puff.position.set(part * 8, Math.sin(part) * 2, part % 2 * 5);
      puff.scale.y = .45;
      cloud.add(puff);
    }
    cloud.position.set(Math.sin(index * 2.3) * 260, 75 + index % 4 * 8, Math.cos(index * 2.3) * 260);
    scene.add(cloud);
    clouds.push(cloud);
  }
  const dock = new THREE.Mesh(new THREE.BoxGeometry(10, 1, 30), bark);
  dock.position.set(0, 1, 65);
  scene.add(dock);
  return { water, islands, beacons, clouds };
}
