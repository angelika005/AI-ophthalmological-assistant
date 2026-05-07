import React, { useState, useEffect, useRef } from 'react';

interface LazyImageProps {
  src: string;
  alt: string;
  placeholder?: string;
  className?: string;
  width?: number | string;
  height?: number | string;
  onLoad?: () => void;
}

/**
 * Компонент для ленивой загрузки изображений
 * Использует Intersection Observer для отложенной загрузки при входе в viewport
 * Поддерживает native loading="lazy" как fallback
 * 
 */
export const LazyImage: React.FC<LazyImageProps> = ({
  src,
  alt,
  placeholder,
  className,
  width,
  height,
  onLoad
}) => {
  const [imageSrc, setImageSrc] = useState<string>(placeholder || src);
  const [isLoaded, setIsLoaded] = useState<boolean>(!placeholder);
  const [isError, setIsError] = useState<boolean>(false);
  const imgRef = useRef<HTMLImageElement>(null);

  useEffect(() => {
    const observer = new IntersectionObserver(
      (entries) => {
        entries.forEach((entry) => {
          if (entry.isIntersecting) {
            const img = entry.target as HTMLImageElement;
            img.src = src;
            img.onload = () => {
              setIsLoaded(true);
              setImageSrc(src);
              onLoad?.();
            };
            img.onerror = () => {
              setIsError(true);
            };
            observer.unobserve(img);
          }
        });
      },
      { threshold: 0.1, rootMargin: '50px' }
    );

    if (imgRef.current) {
      observer.observe(imgRef.current);
    }

    return () => {
      observer.disconnect();
    };
  }, [src, onLoad]);

  return (
    <img
      ref={imgRef}
      src={imageSrc}
      alt={alt}
      className={`${className || ''} ${isLoaded ? 'loaded' : 'loading'} ${isError ? 'error' : ''}`}
      width={width}
      height={height}
      loading="lazy"
    />
  );
};

export default LazyImage;
