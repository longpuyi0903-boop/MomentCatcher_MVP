import { useEffect, useState } from 'react'
import { useBackgroundStore } from '../store/backgroundStore'
import './MomentCard.css'

function MomentCard({ card, onClose }) {
  const [isVisible, setIsVisible] = useState(false)
  const selectedBackground = useBackgroundStore((state) => state.selectedBackground)

  useEffect(() => {
    // 浮现动画
    setTimeout(() => setIsVisible(true), 10)
  }, [])

  if (!card) return null

  // 获取情绪颜色
  const getEmotionColor = (emotion) => {
    const emotionMap = {
      'joy': 'var(--emotion-joy)',
      'sadness': 'var(--emotion-sadness)',
      'anger': 'var(--emotion-anger)',
      'fear': 'var(--emotion-fear)',
      'love': 'var(--emotion-love)',
      'surprise': 'var(--emotion-surprise)',
      'neutral': 'var(--emotion-neutral)',
    }
    return emotionMap[emotion?.toLowerCase()] || emotionMap['neutral']
  }

  const borderColor = card.color || getEmotionColor(card.emotion)

  // 格式化日期 - 1:1 复刻参考代码
  const formattedDate = card.timestamp 
    ? new Date(card.timestamp).toLocaleDateString('en-US', {
        year: 'numeric',
        month: '2-digit',
        day: '2-digit'
      }).replace(/\//g, '.')
    : ''

  // 从背景路径提取文件名（大写）
  const getBackgroundName = () => {
    if (!selectedBackground) return ''
    // 从路径中提取文件名，例如 "/星体素材/miller.png" -> "MILLER"
    const fileName = selectedBackground.split('/').pop() || ''
    const nameWithoutExt = fileName.replace(/\.[^/.]+$/, '') // 移除扩展名
    return nameWithoutExt.toUpperCase()
  }

  const backgroundName = getBackgroundName()

  return (
    <div className={`moment-card-overlay ${isVisible ? 'visible' : ''}`} onClick={onClose}>
      <div 
        className={`moment-card ${isVisible ? 'visible' : ''}`}
        onClick={(e) => e.stopPropagation()}
      >
        {/* 左侧竖条 - 1:1 复刻参考代码 */}
        <div className="moment-card-accent-bar" style={{ backgroundColor: `${borderColor}99` }}></div>
        
        <div className="moment-card-inner">
          <button className="moment-card-close" onClick={onClose}>
            <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2.5}>
              <path strokeLinecap="round" strokeLinejoin="round" d="M6 18L18 6M6 6l12 12" />
            </svg>
          </button>
          
          {/* Header Row: Title & Date - 1:1 复刻参考代码 */}
          <div className="moment-card-header">
            <h2 className="moment-card-title">{card.title || 'Untitled Moment'}</h2>
            <span className="moment-card-date">{formattedDate}</span>
          </div>

          {/* Separator line - 1:1 复刻参考代码 */}
          <div className="moment-card-separator"></div>

          {/* Main Content - 1:1 复刻参考代码 */}
          <div className="moment-card-content">
            <p className="moment-card-summary">"{card.summary || 'No summary available.'}"</p>
          </div>

          {/* Footer Data Tags - 1:1 复刻参考代码 */}
          <div className="moment-card-footer">
            <div className="moment-card-footer-tag">{backgroundName || 'UNKNOWN'}</div>
            <div className="moment-card-footer-tag">LOG_REF_{card.id || 'N/A'}</div>
            <button className="moment-card-download" onClick={() => {
              // 下载功能可以在这里实现
              console.log('Download moment:', card.id)
            }}>
              <svg className="w-3.5 h-3.5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M3 16.5v2.25A2.25 2.25 0 005.25 21h13.5A2.25 2.25 0 0021 18.75V16.5M16.5 12L12 16.5m0 0L7.5 12m4.5 4.5V3" />
              </svg>
            </button>
          </div>
        </div>
      </div>
    </div>
  )
}

export default MomentCard


