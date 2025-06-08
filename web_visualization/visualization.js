
        let scene, camera, renderer, controls;
        let objects = new Map();

        function init() {
            // Create scene
            scene = new THREE.Scene();
            scene.background = new THREE.Color(0x000000);

            // Create camera
            camera = new THREE.PerspectiveCamera(75, window.innerWidth / window.innerHeight, 0.1, 1000);
            camera.position.z = 5;

            // Create renderer
            renderer = new THREE.WebGLRenderer();
            renderer.setSize(window.innerWidth, window.innerHeight);
            document.body.appendChild(renderer.domElement);

            // Add orbit controls
            controls = new THREE.OrbitControls(camera, renderer.domElement);
            controls.enableDamping = true;
            controls.dampingFactor = 0.05;

            // Add ambient light
            const ambientLight = new THREE.AmbientLight(0x404040);
            scene.add(ambientLight);

            // Add directional light
            const directionalLight = new THREE.DirectionalLight(0xffffff, 0.5);
            directionalLight.position.set(1, 1, 1);
            scene.add(directionalLight);

            // Handle window resize
            window.addEventListener('resize', onWindowResize, false);

            // Start animation loop
            animate();
        }

        function onWindowResize() {
            camera.aspect = window.innerWidth / window.innerHeight;
            camera.updateProjectionMatrix();
            renderer.setSize(window.innerWidth, window.innerHeight);
        }

        function animate() {
            requestAnimationFrame(animate);
            controls.update();
            renderer.render(scene, camera);
        }

        // WebSocket connection
        const ws = new WebSocket('ws://' + window.location.hostname + ':8765');
        
        ws.onmessage = function(event) {
            const data = JSON.parse(event.data);
            
            switch(data.type) {
                case 'add':
                    addObject(data.id, data.position, data.color, data.model_type, data.scale);
                    break;
                case 'update':
                    updateObject(data.id, data.position, data.color, data.rotation, data.scale);
                    break;
                case 'remove':
                    removeObject(data.id);
                    break;
            }
        };

        function addObject(id, position, color, modelType, scale) {
            let geometry;
            switch(modelType) {
                case 'cube':
                    geometry = new THREE.BoxGeometry(scale[0], scale[1], scale[2]);
                    break;
                case 'sphere':
                    geometry = new THREE.SphereGeometry(scale[0], 32, 32);
                    break;
                default:
                    geometry = new THREE.BoxGeometry(1, 1, 1);
            }

            const material = new THREE.MeshPhongMaterial({ color: new THREE.Color(color[0], color[1], color[2]) });
            const mesh = new THREE.Mesh(geometry, material);
            mesh.position.set(position[0], position[1], position[2]);
            
            scene.add(mesh);
            objects.set(id, mesh);
        }

        function updateObject(id, position, color, rotation, scale) {
            const mesh = objects.get(id);
            if (mesh) {
                mesh.position.set(position[0], position[1], position[2]);
                mesh.material.color.setRGB(color[0], color[1], color[2]);
                if (rotation) {
                    mesh.rotation.set(rotation[0], rotation[1], rotation[2]);
                }
                if (scale) {
                    mesh.scale.set(scale[0], scale[1], scale[2]);
                }
            }
        }

        function removeObject(id) {
            const mesh = objects.get(id);
            if (mesh) {
                scene.remove(mesh);
                mesh.geometry.dispose();
                mesh.material.dispose();
                objects.delete(id);
            }
        }

        init();
        