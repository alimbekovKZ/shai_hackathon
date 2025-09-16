import { Header } from "@/components/header"
import { HeroSection } from "@/components/hero-section"
import { FeatureHighlights } from "@/components/feature-highlights"
import { Footer } from "@/components/footer"

export default function Home() {
  return (
    <main className="min-h-screen bg-background">
      <Header />
      <HeroSection />
      <FeatureHighlights />
      <Footer />
    </main>
  )
}
