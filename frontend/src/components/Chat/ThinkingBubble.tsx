import { useState, useEffect } from 'react';
import { motion, AnimatePresence } from 'framer-motion';

const steps = ['Planning', 'Researching', 'Generating'];

export function ThinkingBubble() {
  const [currentStep, setCurrentStep] = useState(0);

  useEffect(() => {
    const interval = setInterval(() => {
      setCurrentStep((prev) => (prev < steps.length - 1 ? prev + 1 : prev));
    }, 1500);
    return () => clearInterval(interval);
  }, []);

  return (
    <div className="flex flex-col space-y-2 py-2 max-w-sm">
      {steps.map((step, index) => {
        const isPast = index < currentStep;
        const isActive = index === currentStep;

        return (
          <div key={step} className="flex items-center space-x-3 text-[11px] font-mono tracking-widest uppercase">
            <div className="w-24 text-text-muted text-right">
              {step}
            </div>
            <div className="flex-1 flex items-center space-x-1">
              <AnimatePresence>
                {[...Array(8)].map((_, i) => (
                  <motion.div
                    key={i}
                    initial={{ opacity: 0, scale: 0.5 }}
                    animate={{ 
                      opacity: isPast || (isActive && i <= 4) ? 1 : 0.2, 
                      scale: 1,
                      backgroundColor: isActive ? '#3b82f6' : isPast ? '#22c55e' : '#374151'
                    }}
                    transition={{
                      duration: 0.2,
                      delay: isActive ? i * 0.1 : 0,
                    }}
                    className="w-2 h-4 rounded-[1px]"
                  />
                ))}
              </AnimatePresence>
            </div>
          </div>
        );
      })}
    </div>
  );
}
