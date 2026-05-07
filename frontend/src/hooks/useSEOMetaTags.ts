import { useEffect } from 'react';

export interface SEOMetaTagsConfig {
  title: string;
  description: string;
  canonical?: string;
  ogTitle?: string;
  ogDescription?: string;
  ogImage?: string;
  ogType?: 'website' | 'article' | 'product';
  robotsDirective?: 'index, follow' | 'noindex, follow' | 'noindex, nofollow';
  keywords?: string;
  twitterCard?: 'summary' | 'summary_large_image' | 'app';
  twitterTitle?: string;
  twitterDescription?: string;
  twitterImage?: string;
}

/**
 * Hook для управления SEO мета-тегами
 * Динамически обновляет title, meta description, canonical URL, Open Graph и Twitter Card теги
 */
export const useSEOMetaTags = (config: SEOMetaTagsConfig): void => {
  useEffect(() => {
    // ========== Обновление Title ==========
    document.title = config.title;

    // ========== Обновление Meta Description ==========
    let metaDescription = document.querySelector('meta[name="description"]');
    if (!metaDescription) {
      metaDescription = document.createElement('meta');
      metaDescription.setAttribute('name', 'description');
      document.head.appendChild(metaDescription);
    }
    metaDescription.setAttribute('content', config.description);

    // ========== Обновление Canonical URL ==========
    if (config.canonical) {
      let canonical = document.querySelector('link[rel="canonical"]');
      if (!canonical) {
        canonical = document.createElement('link');
        canonical.setAttribute('rel', 'canonical');
        document.head.appendChild(canonical);
      }
      canonical.setAttribute('href', config.canonical);
    }

    // ========== Обновление Keywords ==========
    if (config.keywords) {
      let metaKeywords = document.querySelector('meta[name="keywords"]');
      if (!metaKeywords) {
        metaKeywords = document.createElement('meta');
        metaKeywords.setAttribute('name', 'keywords');
        document.head.appendChild(metaKeywords);
      }
      metaKeywords.setAttribute('content', config.keywords);
    }

    // ========== Обновление Robots Directive ==========
    if (config.robotsDirective) {
      let robotsMeta = document.querySelector('meta[name="robots"]');
      if (!robotsMeta) {
        robotsMeta = document.createElement('meta');
        robotsMeta.setAttribute('name', 'robots');
        document.head.appendChild(robotsMeta);
      }
      robotsMeta.setAttribute('content', config.robotsDirective);
    }

    // ========== Обновление Open Graph Meta Tags ==========
    const ogTags = [
      { property: 'og:title', content: config.ogTitle || config.title },
      { property: 'og:description', content: config.ogDescription || config.description },
      { property: 'og:type', content: config.ogType || 'website' },
      { property: 'og:url', content: window.location.href },
    ];

    if (config.ogImage) {
      ogTags.push({ property: 'og:image', content: config.ogImage });
      ogTags.push({ property: 'og:image:alt', content: 'AI Ophthalmological Assistant' });
    }

    ogTags.forEach(tag => {
      let ogMeta = document.querySelector(`meta[property="${tag.property}"]`);
      if (!ogMeta) {
        ogMeta = document.createElement('meta');
        ogMeta.setAttribute('property', tag.property);
        document.head.appendChild(ogMeta);
      }
      ogMeta.setAttribute('content', tag.content);
    });

    // ========== Обновление Twitter Card Meta Tags ==========
    if (config.twitterCard) {
      const twitterTags = [
        { name: 'twitter:card', content: config.twitterCard },
        { name: 'twitter:title', content: config.twitterTitle || config.title },
        { name: 'twitter:description', content: config.twitterDescription || config.description },
      ];

      if (config.twitterImage) {
        twitterTags.push({ name: 'twitter:image', content: config.twitterImage });
      }

      twitterTags.forEach(tag => {
        let twitterMeta = document.querySelector(`meta[name="${tag.name}"]`);
        if (!twitterMeta) {
          twitterMeta = document.createElement('meta');
          twitterMeta.setAttribute('name', tag.name);
          document.head.appendChild(twitterMeta);
        }
        twitterMeta.setAttribute('content', tag.content);
      });
    }

    // Cleanup: удаляем дублирующиеся мета-теги при размонтировании
    return () => {
      // Мета-теги остаются для корректной работы при переходе между страницами
    };
  }, [config]);
};
