"use client";
import React from "react";
import { Newspaper } from "lucide-react";

// Define the structure of a single news article
interface NewsArticle {
  title: string;
  url: string;
  snippet?: string;
  source?: string;
  publishedAt?: string;
}

// Define your StreamEvent type
export interface StreamEvent {
  type: string;
  data?: NewsArticle[]; // properly typed now
}

interface NewsSidebarProps {
  events: StreamEvent[];
  heading?: string;
}

export const NewsSidebar: React.FC<NewsSidebarProps> = ({
  events,
  heading = "Latest News",
}) => {
  // Filter only news-related events
  const newsEvents = events.filter(
    (event): event is StreamEvent & { data: NewsArticle[] } =>
      event.type === "news_results" && Array.isArray(event.data),
  );

  // Flatten all articles into a single array
  const articles: NewsArticle[] = newsEvents.flatMap((event) => event.data);

  return (
    <div className="w-full bg-black/80 backdrop-blur-md border border-white/10 rounded-xl shadow-lg p-4 space-y-3">
      {/* Header */}
      <div className="flex items-center gap-2 mb-2 border-b border-white/10 pb-2">
        <Newspaper className="w-5 h-5 text-purple-400" />
        <h2 className="text-lg font-semibold text-white/90">{heading}</h2>
      </div>

      {/* If no articles */}
      {articles.length === 0 ? (
        <p className="text-white/50 text-sm italic text-center py-6">
          No recent news articles found.
        </p>
      ) : (
        <div className="space-y-3 overflow-y-auto max-h-[80vh] no-scrollbar">
          {articles.map((article, idx) => (
            <div
              key={idx}
              className="p-3 border border-white/10 rounded-lg bg-white/5 hover:bg-white/10 transition-all duration-300 cursor-pointer group"
            >
              {/* Article Title */}
              <a
                href={article.url}
                target="_blank"
                rel="noopener noreferrer"
                className="text-white/90 group-hover:text-purple-400 font-medium text-sm underline-offset-2 hover:underline"
              >
                {article.title}
              </a>

              {/* Snippet */}
              {article.snippet && (
                <p className="text-white/60 text-xs mt-2 leading-snug">
                  {article.snippet.length > 140
                    ? `${article.snippet.slice(0, 140)}...`
                    : article.snippet}
                </p>
              )}

              {/* Optional metadata */}
              {(article.source || article.publishedAt) && (
                <div className="mt-2 flex items-center justify-between text-[11px] text-white/40">
                  {article.source && <span>{article.source}</span>}
                  {article.publishedAt && (
                    <span>
                      {new Date(article.publishedAt).toLocaleDateString()}
                    </span>
                  )}
                </div>
              )}
            </div>
          ))}
        </div>
      )}
    </div>
  );
};
