'use client'

import { useRef, useMemo, useEffect } from 'react'
import { Canvas, useFrame, useThree } from '@react-three/fiber'
import { OrbitControls } from '@react-three/drei'
import * as THREE from 'three'

// Neural network layer nodes with flowing particles
function NeuralNetwork() {
  const pointsRef = useRef<THREE.Points>(null!)
  const linesRef = useRef<THREE.Group>(null!)
  const mouseRef = useRef({ x: 0, y: 0 })
  const { viewport } = useThree()

  // Track mouse position
  useEffect(() => {
    const handleMouse = (e: MouseEvent) => {
      mouseRef.current.x = (e.clientX / window.innerWidth) * 2 - 1
      mouseRef.current.y = -(e.clientY / window.innerHeight) * 2 + 1
    }
    window.addEventListener('mousemove', handleMouse)
    return () => window.removeEventListener('mousemove', handleMouse)
  }, [])

  // Create neural network layers
  const { nodes, connections, particles } = useMemo(() => {
    const layers = [
      { count: 4, label: 'Input', x: -4 },
      { count: 6, label: 'Embedding', x: -2 },
      { count: 8, label: 'Temporal', x: 0 },
      { count: 6, label: 'Attention', x: 2 },
      { count: 3, label: 'Output', x: 4 },
    ]

    const nodes: THREE.Vector3[] = []
    const connections: Array<[THREE.Vector3, THREE.Vector3]> = []
    const particles: THREE.Vector3[] = []

    let prevLayerNodes: THREE.Vector3[] = []

    layers.forEach((layer) => {
      const layerNodes: THREE.Vector3[] = []
      const spacing = 1.2
      const totalHeight = (layer.count - 1) * spacing
      const startY = -totalHeight / 2

      for (let i = 0; i < layer.count; i++) {
        const node = new THREE.Vector3(layer.x, startY + i * spacing, 0)
        layerNodes.push(node)
        nodes.push(node)
      }

      // Create connections from previous layer
      if (prevLayerNodes.length > 0) {
        prevLayerNodes.forEach((prevNode) => {
          layerNodes.forEach((currNode) => {
            connections.push([prevNode.clone(), currNode.clone()])
          })
        })
      }

      prevLayerNodes = layerNodes
    })

    // Create flowing particles along connections
    for (let i = 0; i < 200; i++) {
      const connIdx = Math.floor(Math.random() * connections.length)
      const [from, to] = connections[connIdx]
      const t = Math.random()
      const pos = new THREE.Vector3().lerpVectors(from, to, t)
      particles.push(pos)
    }

    return { nodes, connections, particles }
  }, [])

  // Node positions for points geometry
  const nodePositions = useMemo(() => {
    const arr = new Float32Array(nodes.length * 3)
    nodes.forEach((n, i) => {
      arr[i * 3] = n.x
      arr[i * 3 + 1] = n.y
      arr[i * 3 + 2] = n.z
    })
    return arr
  }, [nodes])

  // Line geometry
  const lineGeometry = useMemo(() => {
    const positions: number[] = []
    connections.forEach(([from, to]) => {
      positions.push(from.x, from.y, from.z)
      positions.push(to.x, to.y, to.z)
    })
    const geom = new THREE.BufferGeometry()
    geom.setAttribute('position', new THREE.Float32BufferAttribute(positions, 3))
    return geom
  }, [connections])

  // Mouse reactive rotation
  useFrame((state, delta) => {
    const mouse = mouseRef.current

    if (linesRef.current) {
      linesRef.current.position.x += (mouse.x * 0.5 - linesRef.current.position.x) * 0.05
      linesRef.current.position.y += (mouse.y * 0.3 - linesRef.current.position.y) * 0.05
    }

    if (pointsRef.current) {
      // Pulse node sizes
      const material = pointsRef.current.material as THREE.ShaderMaterial
      if (material.uniforms) {
        material.uniforms.uTime.value += delta
        material.uniforms.uMouse.value.lerp(
          new THREE.Vector2(mouse.x, mouse.y),
          0.1
        )
      }
    }
  })

  // Shader for glowing nodes
  const shaderMaterial = useMemo(() => {
    return new THREE.ShaderMaterial({
      uniforms: {
        uTime: { value: 0 },
        uColor: { value: new THREE.Color('#2563EB') },
        uMouse: { value: new THREE.Vector2(0, 0) },
      },
      vertexShader: `
        varying vec2 vUv;
        varying vec3 vPosition;
        void main() {
          vUv = uv;
          vPosition = position;
          gl_Position = projectionMatrix * modelViewMatrix * vec4(position, 1.0);
          gl_PointSize = 8.0;
        }
      `,
      fragmentShader: `
        varying vec2 vUv;
        varying vec3 vPosition;
        uniform float uTime;
        uniform vec3 uColor;
        uniform vec2 uMouse;
        void main() {
          float dist = length(gl_PointCoord - vec2(0.5));
          if (dist > 0.5) discard;
          float glow = exp(-dist * 4.0) * 0.8;
          float pulse = 0.5 + 0.5 * sin(uTime * 2.0 + vPosition.x * 2.0 + vPosition.y);
          float alpha = glow * (0.3 + pulse * 0.5);
          gl_FragColor = vec4(uColor, alpha);
        }
      `,
      transparent: true,
      depthWrite: false,
      blending: THREE.AdditiveBlending,
    })
  }, [])

  return (
    <group ref={linesRef}>
      {/* Connection lines */}
      <lineSegments geometry={lineGeometry}>
        <lineBasicMaterial
          color="#2563EB"
          transparent
          opacity={0.06}
          depthWrite={false}
        />
      </lineSegments>

      {/* Nodes */}
      <points ref={pointsRef}>
        <bufferGeometry>
          <bufferAttribute
            attach="attributes-position"
            array={nodePositions}
            count={nodes.length}
            itemSize={3}
          />
        </bufferGeometry>
        <primitive object={shaderMaterial} attach="material" />
      </points>
    </group>
  )
}

function ParticleField() {
  const count = 500
  const positions = useMemo(() => {
    const arr = new Float32Array(count * 3)
    for (let i = 0; i < count; i++) {
      arr[i * 3] = (Math.random() - 0.5) * 20
      arr[i * 3 + 1] = (Math.random() - 0.5) * 12
      arr[i * 3 + 2] = (Math.random() - 0.5) * 6
    }
    return arr
  }, [])

  const ref = useRef<THREE.Points>(null!)

  useFrame((_, delta) => {
    if (ref.current) {
      ref.current.rotation.y += delta * 0.02
    }
  })

  return (
    <points ref={ref}>
      <bufferGeometry>
        <bufferAttribute
          attach="attributes-position"
          array={positions}
          count={count}
          itemSize={3}
        />
      </bufferGeometry>
      <pointsMaterial
        size={0.015}
        color="#2563EB"
        transparent
        opacity={0.3}
        depthWrite={false}
        blending={THREE.AdditiveBlending}
      />
    </points>
  )
}

export function NeuralNetworkCanvas() {
  return (
    <div className="absolute inset-0 z-0">
      <Canvas
        camera={{ position: [0, 0, 8], fov: 50 }}
        gl={{
          antialias: true,
          alpha: true,
          powerPreference: 'high-performance',
        }}
        dpr={[1, 2]}
      >
        <ambientLight intensity={0.1} />
        <NeuralNetwork />
        <ParticleField />
        <OrbitControls
          enableZoom={false}
          enablePan={false}
          enableRotate={false}
          autoRotate
          autoRotateSpeed={0.15}
        />
      </Canvas>
      {/* Gradient overlays for blending */}
      <div className="absolute inset-0 bg-gradient-to-b from-background/60 via-transparent to-background pointer-events-none" />
      <div className="absolute inset-0 bg-gradient-hero pointer-events-none" />
    </div>
  )
}
