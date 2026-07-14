import { BrowserRouter, Routes, Route } from 'react-router-dom'
import './App.css'
import Nav from './nav'
import Schedule from './components/Schedule'
import Teachers from './components/Teachers'
import Students from './components/Students'
import Rooms from './components/Rooms'

function App() {
  return (
    <BrowserRouter>
      <Nav />
      <main className="container py-4">
        <Routes>
          <Route path="/" element={<Schedule />} />
          <Route path="/teachers" element={<Teachers />} />
          <Route path="/students" element={<Students />} />
          <Route path="/rooms" element={<Rooms />} />
        </Routes>
      </main>
    </BrowserRouter>
  )
}

export default App
