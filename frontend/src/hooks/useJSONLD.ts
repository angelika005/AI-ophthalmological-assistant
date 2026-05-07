import { useEffect } from 'react';

export interface JSONLDConfig {
  type: string;
  data: Record<string, any>;
}

/**
 * Hook для добавления JSON-LD структурированных данных в <head>
 * Использование для улучшения показа в поисковой выдаче и SEO
 * 
 * @param config - конфигурация JSON-LD
 * 
 * @example
 * useJSONLD({
 *   type: 'MedicalService',
 *   data: {
 *     name: 'Диагностика глаукомы',
 *     description: 'Онлайн диагностика...'
 *   }
 * });
 */
export const useJSONLD = (config: JSONLDConfig): void => {
  useEffect(() => {
    const script = document.createElement('script');
    script.type = 'application/ld+json';
    script.innerHTML = JSON.stringify({
      '@context': 'https://schema.org',
      '@type': config.type,
      ...config.data
    });
    
    // Удаляем старый JSON-LD скрипт если существует
    const oldScripts = document.querySelectorAll(
      `script[type="application/ld+json"][data-seo-type="${config.type}"]`
    );
    oldScripts.forEach(s => s.remove());

    script.setAttribute('data-seo-type', config.type);
    document.head.appendChild(script);

    return () => {
      script.remove();
    };
  }, [config]);
};
