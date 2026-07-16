import 'bootstrap/dist/css/bootstrap.min.css'
import 'bootstrap/dist/js/bootstrap.bundle.min.js'
import { StrictMode } from 'react'
import { createRoot } from 'react-dom/client'
import './index.css'
import App from './App.jsx'
import logo from './assets/favicon-copia.png'

document.title = "FOM Scheduler";

const updateFavicon = (newIconPath) => {
  let link = document.querySelector("link[rel*='icon']");
  if (!link) {
    link = document.createElement('link');
    link.rel = 'icon';
    document.head.appendChild(link);
  }
  link.href = newIconPath;
};
updateFavicon(logo);

createRoot(document.getElementById('root')).render(
  <StrictMode>
    <App />
    {/* <Nav /> */}
  </StrictMode>,
)
