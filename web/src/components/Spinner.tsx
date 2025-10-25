import React from 'react'

interface SpinnerProps {
  size?: 'sm' | 'md' | 'lg'
  className?: string
}

export const Spinner: React.FC<SpinnerProps> = ({ size = 'md', className = '' }) => {
  const sizeClasses = {
    sm: 'h-4 w-4',
    md: 'h-8 w-8',
    lg: 'h-12 w-12'
  }

  return (
    <div className={`${sizeClasses[size]} ${className}`}>
      <div className="relative w-full h-full">
        {/* Outer ring */}
        <div className="absolute inset-0 rounded-full border-2 border-accent/20"></div>
        
        {/* Spinning ring */}
        <div className="absolute inset-0 rounded-full border-2 border-transparent border-t-accent animate-spin"></div>
        
        {/* Inner pulse */}
        <div className="absolute inset-1 rounded-full bg-accent/10 animate-pulse"></div>
      </div>
    </div>
  )
}

interface LoadingSpinnerProps {
  message?: string
  size?: 'sm' | 'md' | 'lg'
}

export const LoadingSpinner: React.FC<LoadingSpinnerProps> = ({ 
  message = 'Loading...', 
  size = 'md' 
}) => {
  return (
    <div className="flex flex-col items-center justify-center space-y-3">
      <Spinner size={size} />
      <p className="text-primaryText text-sm font-medium animate-pulse">
        {message}
      </p>
    </div>
  )
}
