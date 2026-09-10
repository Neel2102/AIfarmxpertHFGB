import React, { useEffect } from 'react';

import Navbar from './Navbar';
import HeroSection from './sections/HeroSection';
import AgentsSection from './sections/AgentsSection';
import FeaturesSection from './sections/FeaturesSection';
import HowItWorksSection from './sections/HowItWorksSection';
import TechSection from './sections/TechSection';
import ChipSceneSection from './sections/ChipSceneSection';
import CTASection from './sections/CTASection';
import Footer from './Footer';

import '../styles/landingpage.css';

export default function LandingPage() {
  useEffect(() => {
    // ══ SCROLL REVEAL ══
    const reveals = document.querySelectorAll('.reveal');
    const revObs = new IntersectionObserver(
      (entries) => {
        entries.forEach((e) => { if (e.isIntersecting) e.target.classList.add('visible'); });
      },
      { threshold: 0.12 }
    );
    reveals.forEach((r) => revObs.observe(r));

    return () => {
      revObs.disconnect();
    };
  }, []);

  return (
    <>
      <Navbar />
      <HeroSection />
      <AgentsSection />
      <FeaturesSection />
      <HowItWorksSection />
      <TechSection />
      <ChipSceneSection />
      <CTASection />
      <Footer />
    </>
  );
}