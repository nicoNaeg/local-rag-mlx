"use client";

import { useEffect, useRef, useState, type FormEvent, type ReactNode } from "react";
import { readSSE } from "@/lib/sse";

type Source = {
  id: number;
  doc: string;
  section: string;
  pages: number[];
  score: number;
  text: string;
};

type Metrics = {
  retrieval_ms: number;
  first_token_ms: number;
  total_ms: number;
  tokens: number;
  tokens_per_second: number;
};

type Phase = "idle" | "searching" | "streaming" | "done" | "error";

const EXAMPLES = [
  "Quel est le plafond de remboursement d'un repas en déplacement ?",
  "Quelle est l'indemnité kilométrique pour un véhicule personnel ?",
  "Quand peut-on demander une avance sur frais ?",
];

const fr = (value: number, digits = 0) =>
  value.toLocaleString("fr-FR", { maximumFractionDigits: digits });

export default function Home() {
  const [question, setQuestion] = useState("");
  const [asked, setAsked] = useState("");
  const [phase, setPhase] = useState<Phase>("idle");
  const [sources, setSources] = useState<Source[]>([]);
  const [answer, setAnswer] = useState("");
  const [metrics, setMetrics] = useState<Metrics | null>(null);
  const [error, setError] = useState("");
  const [online, setOnline] = useState<boolean | null>(null);
  const [openId, setOpenId] = useState<number | null>(null);
  const [flash, setFlash] = useState<{ id: number; nonce: number } | null>(null);

  const abortRef = useRef<AbortController | null>(null);
  const cardRefs = useRef(new Map<number, HTMLElement>());

  useEffect(() => {
    fetch("/healthz")
      .then((response) => response.json())
      .then((body) => setOnline(body.status === "ok"))
      .catch(() => setOnline(false));
  }, []);

  async function ask(text: string) {
    const trimmed = text.trim();
    if (!trimmed) return;
    abortRef.current?.abort();
    const controller = new AbortController();
    abortRef.current = controller;

    setAsked(trimmed);
    setPhase("searching");
    setSources([]);
    setAnswer("");
    setMetrics(null);
    setError("");
    setOpenId(null);
    setFlash(null);

    try {
      const response = await fetch("/api/query", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ question: trimmed }),
        signal: controller.signal,
      });
      if (response.status === 503) {
        setError("La file de génération est pleine. Réessayez dans quelques secondes.");
        setPhase("error");
        return;
      }
      if (!response.ok || !response.body) {
        setError(`Le moteur a répondu ${response.status}. Vérifiez que l'API tourne (make api).`);
        setPhase("error");
        return;
      }
      for await (const message of readSSE(response.body)) {
        if (message.event === "sources") {
          setSources(JSON.parse(message.data) as Source[]);
          setPhase("streaming");
        } else if (message.event === "token") {
          const { text: delta } = JSON.parse(message.data) as { text: string };
          setAnswer((previous) => previous + delta);
        } else if (message.event === "done") {
          setMetrics(JSON.parse(message.data) as Metrics);
          setPhase("done");
        } else if (message.event === "error") {
          const { message: detail } = JSON.parse(message.data) as { message: string };
          setError(`La génération a échoué : ${detail}`);
          setPhase("error");
        }
      }
    } catch (cause) {
      if (controller.signal.aborted) return;
      setError("Impossible de joindre le moteur. Lancez l'API avec make api, puis réessayez.");
      setPhase("error");
      console.error(cause);
    }
  }

  function submit(event: FormEvent) {
    event.preventDefault();
    void ask(question);
  }

  function stop() {
    abortRef.current?.abort();
    setPhase(answer ? "done" : "idle");
  }

  function cite(id: number) {
    if (!sources.some((source) => source.id === id)) return;
    setOpenId(id);
    setFlash((previous) => ({ id, nonce: (previous?.nonce ?? 0) + 1 }));
    const card = cardRefs.current.get(id);
    const reduced = window.matchMedia("(prefers-reduced-motion: reduce)").matches;
    card?.scrollIntoView({ behavior: reduced ? "auto" : "smooth", block: "nearest" });
  }

  const busy = phase === "searching" || phase === "streaming";

  return (
    <>
      <header className="border-b border-line">
        <div className="mx-auto flex w-full max-w-5xl items-baseline justify-between px-6 py-5">
          <div className="flex items-baseline gap-3">
            <span className="text-sm font-bold tracking-[0.2em] text-spruce">SOLENCIA</span>
            <span className="hidden text-sm text-ink-muted sm:inline">
              assistance documentaire
            </span>
          </div>
          <span className="flex items-center gap-2 font-mono text-xs text-ink-muted">
            <span
              className={`inline-block size-2 rounded-full ${
                online === null ? "bg-line" : online ? "bg-spruce" : "bg-danger"
              }`}
            />
            {online === null ? "connexion…" : online ? "moteur local" : "moteur hors ligne"}
          </span>
        </div>
      </header>

      <main className="mx-auto w-full max-w-5xl flex-1 px-6 pb-16">
        <form onSubmit={submit} className="py-10">
          <label
            htmlFor="question"
            className="font-mono text-xs tracking-[0.15em] text-ink-muted uppercase"
          >
            Consultation
          </label>
          <div className="mt-3 flex flex-col gap-3 sm:flex-row sm:items-end">
            <input
              id="question"
              name="question"
              value={question}
              onChange={(event) => setQuestion(event.target.value)}
              placeholder="Posez une question sur la documentation interne"
              autoComplete="off"
              className="w-full border-b-2 border-ink bg-transparent pb-2 text-xl outline-none placeholder:text-ink-muted/60 focus:border-spruce md:text-2xl"
            />
            {busy ? (
              <button
                type="button"
                onClick={stop}
                className="shrink-0 border-2 border-spruce px-5 py-2 font-medium text-spruce hover:bg-spruce/10 focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-spruce"
              >
                Arrêter
              </button>
            ) : (
              <button
                type="submit"
                className="shrink-0 border-2 border-spruce bg-spruce px-5 py-2 font-medium text-paper hover:bg-spruce-deep focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-spruce"
              >
                Demander
              </button>
            )}
          </div>
          {phase === "idle" && (
            <div className="mt-6 flex flex-wrap gap-2">
              {EXAMPLES.map((example) => (
                <button
                  key={example}
                  type="button"
                  onClick={() => {
                    setQuestion(example);
                    void ask(example);
                  }}
                  className="border border-line bg-surface px-3 py-1.5 text-sm text-ink-muted hover:border-spruce hover:text-spruce focus-visible:outline-2 focus-visible:outline-spruce"
                >
                  {example}
                </button>
              ))}
            </div>
          )}
        </form>

        {phase !== "idle" && (
          <div className="grid gap-10 md:grid-cols-[3fr_2fr]">
            <section aria-label="Réponse">
              <p className="font-mono text-xs tracking-[0.15em] text-ink-muted uppercase">
                Réponse
              </p>
              <h1 className="mt-2 text-lg font-semibold">{asked}</h1>
              {phase === "searching" && (
                <p className="mt-4 font-mono text-sm text-ink-muted motion-safe:animate-pulse">
                  recherche dans l&apos;index…
                </p>
              )}
              {answer && (
                <p className="mt-4 text-[17px] leading-relaxed whitespace-pre-wrap">
                  {renderAnswer(answer, cite)}
                  {phase === "streaming" && (
                    <span aria-hidden className="text-spruce motion-safe:animate-pulse">
                      ▍
                    </span>
                  )}
                </p>
              )}
              {phase === "streaming" && !answer && (
                <p className="mt-4 font-mono text-sm text-ink-muted motion-safe:animate-pulse">
                  génération…
                </p>
              )}
              {error && (
                <p className="mt-4 border border-danger/40 bg-danger/5 px-4 py-3 text-sm text-danger">
                  {error}
                </p>
              )}
              {metrics && (
                <p className="mt-6 border-t border-line pt-3 font-mono text-xs text-ink-muted">
                  récupération {fr(metrics.retrieval_ms)} ms · premier token{" "}
                  {fr(metrics.first_token_ms)} ms · {fr(metrics.tokens_per_second, 1)} tok/s ·{" "}
                  {fr(metrics.tokens)} tokens
                </p>
              )}
            </section>

            <section aria-label="Sources">
              <p className="font-mono text-xs tracking-[0.15em] text-ink-muted uppercase">
                Sources{sources.length > 0 && ` · ${sources.length}`}
              </p>
              <ul className="mt-2 space-y-3">
                {sources.map((source) => (
                  <li
                    key={`${source.id}:${flash?.id === source.id ? flash.nonce : 0}`}
                    ref={(element) => {
                      if (element) cardRefs.current.set(source.id, element);
                      else cardRefs.current.delete(source.id);
                    }}
                    className={flash?.id === source.id ? "card-flash" : undefined}
                  >
                    <button
                      type="button"
                      aria-expanded={openId === source.id}
                      onClick={() => setOpenId(openId === source.id ? null : source.id)}
                      className="flex w-full items-stretch border border-line bg-surface text-left hover:border-spruce/60 focus-visible:outline-2 focus-visible:outline-spruce"
                    >
                      <span className="flex w-8 shrink-0 items-start justify-center bg-spruce pt-3 font-mono text-sm text-paper">
                        {source.id}
                      </span>
                      <span className="min-w-0 flex-1 p-3">
                        <span className="flex items-baseline justify-between gap-2">
                          <span className="truncate text-sm font-medium">{source.doc}</span>
                          <span className="shrink-0 font-mono text-[11px] text-ink-muted">
                            p. {source.pages.join(", ")}
                          </span>
                        </span>
                        <span className="mt-0.5 block truncate text-xs text-ink-muted">
                          {source.section}
                        </span>
                        <span className="mt-2 flex items-center gap-2">
                          <span className="h-1 flex-1 bg-amber/20">
                            <span
                              className="block h-1 bg-amber"
                              style={{ width: `${Math.round(source.score * 100)}%` }}
                            />
                          </span>
                          <span className="font-mono text-[11px] text-ink-muted">
                            {source.score.toFixed(2)}
                          </span>
                        </span>
                        <span
                          className={`mt-2 block text-sm text-ink-muted ${
                            openId === source.id ? "" : "line-clamp-2"
                          }`}
                        >
                          {source.text}
                        </span>
                      </span>
                    </button>
                  </li>
                ))}
              </ul>
              {phase === "searching" && (
                <p className="mt-2 font-mono text-sm text-ink-muted motion-safe:animate-pulse">
                  recherche hybride + reranking…
                </p>
              )}
            </section>
          </div>
        )}
      </main>

      <footer className="border-t border-line">
        <div className="mx-auto flex w-full max-w-5xl flex-wrap items-baseline justify-between gap-2 px-6 py-4 font-mono text-xs text-ink-muted">
          <span>local-rag-mlx · Qwen3-8B 4-bit via MLX · BGE-M3 + Qdrant</span>
          <span>aucune API cloud à l&apos;exécution</span>
        </div>
      </footer>
    </>
  );
}

function renderAnswer(text: string, cite: (id: number) => void): ReactNode[] {
  return text.split(/\[(\d+)\]/g).map((part, index) =>
    index % 2 === 1 ? (
      <button
        key={index}
        type="button"
        onClick={() => cite(Number(part))}
        aria-label={`Voir la source ${part}`}
        className="inline-block rounded-sm bg-spruce/10 px-1 align-baseline font-mono text-[13px] font-medium text-spruce hover:bg-spruce/20 focus-visible:outline-2 focus-visible:outline-spruce"
      >
        [{part}]
      </button>
    ) : (
      <span key={index}>{part}</span>
    ),
  );
}
