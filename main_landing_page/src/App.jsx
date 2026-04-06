import HeroSection from "./components/HeroSection";
import AgentsSection from "./components/AgentsSection";
import HowItWorks from "./components/HowItWorks";
import TrustBar from "./components/TrustBar";
import Footer from "./components/Footer";

export default function App() {
  return (
    <main className="min-h-screen bg-white overflow-x-hidden">
      <HeroSection />
      <TrustBar />
      <AgentsSection />
      <HowItWorks />
      <Footer />
    </main>
  );
}
