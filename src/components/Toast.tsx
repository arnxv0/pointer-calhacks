import { useEffect } from 'react';
import { motion } from 'framer-motion';
import styled from 'styled-components';

const ToastContainer = styled(motion.div)<{ $type: 'success' | 'error' | 'info' }>`
  display: flex;
  align-items: center;
  gap: ${({ theme }) => theme.spacing.sm};
  padding: ${({ theme }) => theme.spacing.md} ${({ theme }) => theme.spacing.lg};
  background: ${({ theme }) => theme.colors.secondaryDark};
  border-radius: ${({ theme }) => theme.radius.md};
  box-shadow: ${({ theme }) => theme.shadow.lg};
  min-width: 300px;
  border-left: 4px solid ${({ $type, theme }) => 
    $type === 'success' ? theme.colors.successGreen :
    $type === 'error' ? theme.colors.errorRed :
    theme.colors.accentNeon
  };

  .material-icons {
    font-size: 20px;
  }
`;

interface ToastProps {
  message: string;
  type: 'success' | 'error' | 'info';
  onClose: () => void;
}

export default function Toast({ message, type, onClose }: ToastProps) {
  useEffect(() => {
    const timer = setTimeout(onClose, 3000);
    return () => clearTimeout(timer);
  }, [onClose]);

  const iconMap = {
    success: 'check_circle',
    error: 'error',
    info: 'info',
  };

  return (
    <ToastContainer
      $type={type}
      initial={{ opacity: 0, y: 50, scale: 0.8 }}
      animate={{ opacity: 1, y: 0, scale: 1 }}
      exit={{ opacity: 0, scale: 0.8, transition: { duration: 0.2 } }}
    >
      <span className="material-icons">{iconMap[type]}</span>
      <span>{message}</span>
    </ToastContainer>
  );
}
