import { useEffect } from 'react';
import { motion, useMotionValue, useSpring } from 'framer-motion';

export function AmbientBackground() {
  const mouseX = useMotionValue(0);
  const mouseY = useMotionValue(0);

  const springConfig = { damping: 50, stiffness: 200, mass: 1 };
  const glowX = useSpring(mouseX, springConfig);
  const glowY = useSpring(mouseY, springConfig);

  useEffect(() => {
    const handleMouseMove = (e: MouseEvent) => {
      mouseX.set(e.clientX);
      mouseY.set(e.clientY);
    };

    window.addEventListener('mousemove', handleMouseMove);
    return () => {
      window.removeEventListener('mousemove', handleMouseMove);
    };
  }, [mouseX, mouseY]);

  return (
    <div className="absolute inset-0 w-full h-full overflow-hidden select-none pointer-events-none z-[-2] bg-[#090B10]">
      {/* Layer 1: Animated Radial Gradients */}
      <div className="absolute inset-0 bg-radial-gradient opacity-40 mix-blend-screen" />

      {/* Layer 2: Aurora Effect */}
      <div className="absolute inset-0 filter blur-[120px] opacity-25">
        <motion.div
          animate={{
            x: [-100, 100, -100],
            y: [-50, 50, -50],
            scale: [1, 1.2, 1],
          }}
          transition={{
            duration: 25,
            repeat: Infinity,
            ease: "easeInOut",
          }}
          className="absolute -top-40 -left-40 w-[600px] h-[600px] rounded-full bg-gradient-to-tr from-accent/40 via-secondary/20 to-transparent"
        />
        <motion.div
          animate={{
            x: [100, -100, 100],
            y: [50, -50, 50],
            scale: [1.2, 1, 1.2],
          }}
          transition={{
            duration: 30,
            repeat: Infinity,
            ease: "easeInOut",
          }}
          className="absolute -bottom-40 -right-40 w-[650px] h-[650px] rounded-full bg-gradient-to-bl from-secondary/40 via-accent/20 to-transparent"
        />
      </div>

      {/* Layer 3: Noise Texture */}
      <div 
        className="absolute inset-0 opacity-[0.02]"
        style={{
          backgroundImage: `url("data:image/svg+xml,%3Csvg viewBox='0 0 200 200' xmlns='http://www.w3.org/2000/svg'%3E%3Cfilter id='noiseFilter'%3E%3CfeTurbulence type='fractalNoise' baseFrequency='0.8' numOctaves='3' stitchTiles='stitch'/%3E%3C/filter%3E%3Crect width='100%25' height='100%25' filter='url(%23noiseFilter)'/%3E%3C/svg%3E")`,
        }}
      />

      {/* Layer 4: Floating Blurred Lights */}
      <div className="absolute inset-0 filter blur-[80px] opacity-20">
        <motion.div
          animate={{
            y: [0, -30, 0],
            opacity: [0.4, 0.8, 0.4],
          }}
          transition={{
            duration: 15,
            repeat: Infinity,
            ease: "easeInOut",
          }}
          className="absolute top-1/4 left-1/3 w-96 h-96 rounded-full bg-accent/30"
        />
        <motion.div
          animate={{
            y: [0, 45, 0],
            opacity: [0.6, 0.3, 0.6],
          }}
          transition={{
            duration: 18,
            repeat: Infinity,
            ease: "easeInOut",
          }}
          className="absolute top-1/2 right-1/4 w-80 h-80 rounded-full bg-secondary/30"
        />
      </div>

      {/* Layer 5: Mouse-Follow Glow */}
      <motion.div
        className="absolute -translate-x-1/2 -translate-y-1/2 w-[500px] h-[500px] rounded-full bg-radial-glow filter blur-[60px] opacity-[0.15] mix-blend-screen"
        style={{
          left: glowX,
          top: glowY,
          background: 'radial-gradient(circle, rgba(59,130,246,0.4) 0%, rgba(168,85,247,0.1) 50%, rgba(0,0,0,0) 100%)',
        }}
      />
    </div>
  );
}
