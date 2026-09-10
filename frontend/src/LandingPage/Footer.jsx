import React from 'react';
import { Link } from 'react-router-dom';

export default function Footer() {
  return (
    <footer>
      <Link to="/" className="footer-logo">
        Farm<span>X</span>pert
      </Link>

      <div className="footer-copy">
        © {new Date().getFullYear()} FarmXpert. All rights reserved.
      </div>

      <div className="footer-links">
        <Link to="/privacy">Privacy</Link>
        <Link to="/terms">Terms</Link>
        <Link to="/docs">Docs</Link>
        <Link to="/contact">Contact</Link>
      </div>
    </footer>
  );
}
