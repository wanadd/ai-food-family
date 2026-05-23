"use client";

import { useEffect, useState } from "react";

import { SettingsScaffold } from "@/components/settings/SettingsScaffold";
import { fetchLegalDocuments, type LegalDocument } from "@/lib/legal/api";

export default function DocumentsSettingsPage() {
  const [docs, setDocs] = useState<LegalDocument[]>([]);

  useEffect(() => {
    void fetchLegalDocuments().then((r) => setDocs(r.documents));
  }, []);

  return (
    <SettingsScaffold title="Документы">
      {docs.map((doc) => (
        <details
          key={doc.id}
          className="rounded-2xl border border-stone-100 bg-white p-4 shadow-sm"
        >
          <summary className="cursor-pointer font-semibold text-stone-900">
            {doc.title}
          </summary>
          <p className="mt-3 text-sm leading-relaxed text-stone-600">{doc.stub_text}</p>
          <a
            href={doc.url}
            target="_blank"
            rel="noopener noreferrer"
            className="mt-2 inline-block text-sm font-semibold text-emerald-700"
          >
            Открыть на сайте →
          </a>
        </details>
      ))}
    </SettingsScaffold>
  );
}
