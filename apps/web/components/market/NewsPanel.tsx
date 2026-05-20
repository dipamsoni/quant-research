"use client";

import { Newspaper } from "lucide-react";
import { useNews } from "@/hooks/useNews";

interface NewsPanelProps {
  symbol: string | null;
}

export function NewsPanel({ symbol }: NewsPanelProps) {
  const { data: articles = [], isLoading, isError } = useNews(symbol);

  return (
    <div className="border-border flex h-48 shrink-0 flex-col border-t">
      <div className="border-border flex items-center gap-2 border-b px-4 py-1.5">
        <Newspaper className="text-muted-foreground size-3.5" />
        <span className="text-xs font-semibold tracking-tight">
          News{symbol ? ` — ${symbol}` : ""}
        </span>
      </div>

      <div className="flex-1 overflow-y-auto">
        {isLoading && (
          <div className="space-y-2 p-3">
            {Array.from({ length: 4 }).map((_, i) => (
              <div key={i} className="bg-muted h-4 animate-pulse rounded" />
            ))}
          </div>
        )}

        {isError && (
          <div className="text-destructive px-4 py-3 text-xs">
            Failed to load news.
          </div>
        )}

        {!isLoading && !isError && articles.length === 0 && (
          <div className="text-muted-foreground flex flex-col items-center gap-1 py-6 text-center">
            <Newspaper className="size-6 opacity-30" />
            <p className="text-xs">No recent news for {symbol ?? "this asset"}</p>
          </div>
        )}

        {!isLoading && !isError && articles.length > 0 && (
          <ul className="divide-border divide-y text-xs">
            {articles.map((article) => (
              <li key={article.id}>
                <a
                  href={article.url}
                  target="_blank"
                  rel="noopener noreferrer"
                  className="hover:bg-muted/50 flex items-start gap-3 px-4 py-2 transition-colors"
                >
                  <span className="text-muted-foreground mt-0.5 shrink-0 font-mono">
                    {new Date(article.published_at).toLocaleTimeString([], {
                      hour: "2-digit",
                      minute: "2-digit",
                    })}
                  </span>
                  <span className="min-w-0">
                    <span className="line-clamp-2 font-medium leading-snug">
                      {article.headline}
                    </span>
                    <span className="text-muted-foreground mt-0.5 block">
                      {article.source}
                    </span>
                  </span>
                </a>
              </li>
            ))}
          </ul>
        )}
      </div>
    </div>
  );
}
