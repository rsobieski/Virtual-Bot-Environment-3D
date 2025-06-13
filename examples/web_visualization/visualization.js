let scene, camera, renderer, controls;
let objects = new Map();
let ws;

function createSky() {
    // Create a large sphere for the sky
    const skyGeometry = new THREE.SphereGeometry(500, 32, 32);
    const skyMaterial = new THREE.MeshBasicMaterial({
        color: 0x87CEEB,  // Sky blue color
        side: THREE.BackSide  // Render the inside of the sphere
    });
    const sky = new THREE.Mesh(skyGeometry, skyMaterial);
    scene.add(sky);
    console.log('Sky added');
}

function createGround() {
    // Create a large plane for the ground
    const groundGeometry = new THREE.PlaneGeometry(1000, 1000);
    const groundMaterial = new THREE.MeshPhongMaterial({
        color: 0x808080,  // Gray color
        side: THREE.DoubleSide,
        flatShading: true,
        transparent: true,
        opacity: 0.5 // 50% transparency
    });
    const ground = new THREE.Mesh(groundGeometry, groundMaterial);
    
    // Rotate the ground to be horizontal
    ground.rotation.x = -Math.PI / 2;
    ground.position.y = -0.5;  // Slightly below zero to avoid z-fighting
    
    // Add a grid helper to the ground
    const gridHelper = new THREE.GridHelper(1000, 100, 0x000000, 0x000000);
    gridHelper.position.y = -0.49;  // Just above the ground
    scene.add(gridHelper);
    
    scene.add(ground);
    console.log('Ground and grid added');
}

function init() {
    console.log('Starting initialization...');
    try {
        // Create scene
        scene = new THREE.Scene();
        scene.background = new THREE.Color(0x000000);
        console.log('Scene created');

        // Create camera
        camera = new THREE.PerspectiveCamera(75, window.innerWidth / window.innerHeight, 0.1, 1000);
        camera.position.set(5, 5, 5);  // Position camera higher and at an angle
        camera.lookAt(0, 0, 0);
        console.log('Camera created');

        // Create renderer
        renderer = new THREE.WebGLRenderer({ antialias: true });
        renderer.setSize(window.innerWidth, window.innerHeight);
        renderer.shadowMap.enabled = true;  // Enable shadows
        document.body.appendChild(renderer.domElement);
        console.log('Renderer created and added to DOM');

        // Add orbit controls
        controls = new THREE.OrbitControls(camera, renderer.domElement);
        controls.enableDamping = true;
        controls.dampingFactor = 0.05;
        controls.maxPolarAngle = Math.PI / 2;  // Prevent camera from going below ground
        console.log('Controls initialized');

        // Add ambient light
        const ambientLight = new THREE.AmbientLight(0x404040, 0.5);
        scene.add(ambientLight);

        // Add directional light (sun)
        const directionalLight = new THREE.DirectionalLight(0xffffff, 1);
        directionalLight.position.set(50, 50, 50);
        directionalLight.castShadow = true;
        directionalLight.shadow.mapSize.width = 2048;
        directionalLight.shadow.mapSize.height = 2048;
        scene.add(directionalLight);
        console.log('Lights added');

        // Add sky and ground
        createSky();
        createGround();

        // Add a test cube to verify rendering
        const testGeometry = new THREE.BoxGeometry(1, 1, 1);
        const testMaterial = new THREE.MeshPhongMaterial({ color: 0x00ff00 });
        const testCube = new THREE.Mesh(testGeometry, testMaterial);
        scene.add(testCube);
        console.log('Test cube added');

        // Handle window resize
        window.addEventListener('resize', onWindowResize, false);

        // Initialize WebSocket after scene setup
        initWebSocket();

        // Start animation loop
        animate();
        
        console.log('Initialization complete');
    } catch (error) {
        console.error('Error during initialization:', error);
    }
}

function initWebSocket() {
    console.log('Initializing WebSocket connection...');
    try {
        const wsUrl = 'ws://localhost:8765';
        console.log('Connecting to WebSocket at:', wsUrl);
        
        ws = new WebSocket(wsUrl);
        
        ws.onopen = function() {
            console.log('WebSocket connection established successfully');
        };
        
        ws.onerror = function(error) {
            console.error('WebSocket error:', error);
        };
        
        ws.onclose = function(event) {
            console.log('WebSocket connection closed:', event.code, event.reason);
        };
        
        ws.onmessage = function(event) {
            try {
                const data = JSON.parse(event.data);
                console.log('Received WebSocket message:', data);
                
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
            } catch (error) {
                console.error('Error processing WebSocket message:', error);
            }
        };
    } catch (error) {
        console.error('Error initializing WebSocket:', error);
    }
}

function onWindowResize() {
    console.log('Window resized');
    camera.aspect = window.innerWidth / window.innerHeight;
    camera.updateProjectionMatrix();
    renderer.setSize(window.innerWidth, window.innerHeight);
}

function animate() {
    requestAnimationFrame(animate);
    controls.update();
    renderer.render(scene, camera);
}

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

// Initialize everything when the page loads
window.addEventListener('load', function() {
    console.log('Window loaded, starting initialization...');
    init();
});
        