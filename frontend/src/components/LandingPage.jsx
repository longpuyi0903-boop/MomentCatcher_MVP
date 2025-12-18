import { useState } from 'react'
import StarBackground from './StarBackground'
import './LandingPage.css'

function LandingPage({ onInit }) {
  const [userName, setUserName] = useState('')
  const [agentName, setAgentName] = useState('')

  const handleSubmit = (e) => {
    e.preventDefault()
    if (userName.trim() && agentName.trim()) {
      onInit(userName.trim(), agentName.trim())
    }
  }

  return (
    <div className="landing-page">
      <StarBackground />
      
      <div className="landing-container">
        {/* Title Section - Reduced size and muted colors for cinematic depth */}
        <div className="title-section">
          <h1 className="title-line title-line-1 dreamy-font glow-text-dreamy">
            Moment
          </h1>
          <h1 className="title-line title-line-2 dreamy-font glow-text-dreamy">
            Catcher
          </h1>
          <div className="title-divider"></div>
        </div>

        {/* Form Section */}
        <form onSubmit={handleSubmit} className="landing-form">
          <div className="form-group group">
            <label className="form-label">Traveler ID</label>
            <input
              type="text"
              value={userName}
              onChange={(e) => setUserName(e.target.value)}
              placeholder="COOPER"
              className="landing-input"
              required
            />
          </div>
          
          <div className="form-group group">
            <label className="form-label">Companion ID</label>
            <input
              type="text"
              value={agentName}
              onChange={(e) => setAgentName(e.target.value)}
              placeholder="TARS / CASE / BRAND"
              className="landing-input"
              required
            />
          </div>
          
          <button type="submit" className="initiate-btn group">
            <div className="btn-scan"></div>
            <span className="btn-text">Initiate Link</span>
          </button>
        </form>

        {/* Footer / Aesthetic Details */}
        <div className="landing-footer">
          <div className="footer-text">Endurance Mission Control // Sector 04</div>
          <div className="status-indicators">
            <div className="status-dot status-dot-1"></div>
            <div className="status-dot status-dot-2"></div>
            <div className="status-dot status-dot-3"></div>
          </div>
        </div>
      </div>
    </div>
  )
}

export default LandingPage


