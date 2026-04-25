import { Metadata } from "next";

export const metadata: Metadata = {
  title: "Impressum",
  description: "Legal disclosure (Impressum) required by German law.",
};

export default function ImpressumPage() {
  return (
    <div className="min-h-screen bg-white">
      <div className="max-w-3xl mx-auto px-6 py-20">
        <h1 className="text-4xl font-bold text-[#111318] mb-8">Impressum</h1>

        <section className="mb-10">
          <h2 className="text-xl font-semibold text-[#111318] mb-4">Angaben gemass 5 TMG</h2>
          <div className="text-[#4B5563] leading-relaxed space-y-1">
            <p>[Your Full Legal Name]</p>
            <p>[Your Street Address]</p>
            <p>[Your City, Postal Code]</p>
            <p>Germany</p>
          </div>
        </section>

        <section className="mb-10">
          <h2 className="text-xl font-semibold text-[#111318] mb-4">Kontakt</h2>
          <div className="text-[#4B5563] leading-relaxed space-y-1">
            <p>E-Mail: hello@emoratest.com</p>
          </div>
        </section>

        <section className="mb-10">
          <h2 className="text-xl font-semibold text-[#111318] mb-4">Verantwortlich fur den Inhalt nach  55 Abs. 2 RStV</h2>
          <div className="text-[#4B5563] leading-relaxed">
            <p>[Your Full Name]</p>
            <p>[Your Address]</p>
          </div>
        </section>

        <section className="mb-10">
          <h2 className="text-xl font-semibold text-[#111318] mb-4">EU-Streitschlichtung</h2>
          <p className="text-[#4B5563] leading-relaxed">
            Die Europaische Kommission stellt eine Plattform zur
            Online-Streitbeilegung (OS) bereit:
          </p>
          <a
            href="https://ec.europa.eu/consumers/odr"
            target="_blank"
            rel="noopener noreferrer"
            className="text-[#007BFF] hover:underline"
          >
            https://ec.europa.eu/consumers/odr
          </a>
        </section>

        <section>
          <h2 className="text-xl font-semibold text-[#111318] mb-4">Haftungsausschluss</h2>
          <p className="text-[#4B5563] leading-relaxed">
            Trotz sorgfaltiger inhaltlicher Kontrolle ubernehmen wir keine Haftung fur
            die Inhalte externer Links. Fur den Inhalt der verlinkten Seiten sind
            ausschlieBlich deren Betreiber verantwortlich.
          </p>
        </section>

        <div className="mt-16 p-4 bg-[#FFF3CD] border border-[#FFECB5] rounded-lg">
          <p className="text-sm text-[#856404]">
            <strong>TODO:</strong> Replace placeholder values with real legal information.
            This is required by German law (TMG  5).
          </p>
        </div>
      </div>
    </div>
  );
}
