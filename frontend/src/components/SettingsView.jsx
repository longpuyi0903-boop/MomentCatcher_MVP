import { useState } from 'react'
import { updateNamesAPI } from '../services/api'
import './SettingsView.css'

function SettingsView({ userInfo, onClose, onReset, showOverlay = true }) {
  const [isEditing, setIsEditing] = useState(false)
  const [isSaving, setIsSaving] = useState(false)
  const [userName, setUserName] = useState(userInfo.user_name || '')
  const [agentName, setAgentName] = useState(userInfo.agent_name || '')
  const [error, setError] = useState('')
  const [success, setSuccess] = useState('')

  const handleBack = () => {
    if (isEditing) {
      // 如果正在编辑，取消编辑
      setIsEditing(false)
      setUserName(userInfo.user_name || '')
      setAgentName(userInfo.agent_name || '')
      setError('')
      setSuccess('')
    } else {
      // 如果不在编辑，关闭设置页面
      if (onClose) {
        onClose()
      }
    }
  }

  const handleCommit = async () => {
    // COMMIT = 保存重命名
    if (!isEditing) return
    
    if (!userName.trim() || !agentName.trim()) {
      setError('名字不能为空')
      return
    }

    if (userName.trim() === userInfo.user_name && agentName.trim() === userInfo.agent_name) {
      setIsEditing(false)
      // 即使没有变化，也关闭设置页面
      if (onClose) {
        onClose()
      }
      return
    }

    try {
      setIsSaving(true)
      setError('')
      setSuccess('')

      const result = await updateNamesAPI(
        userInfo.user_id,
        userName.trim(),
        agentName.trim()
      )

      if (result.success) {
        setSuccess('名字已更新')
        setIsEditing(false)
        
        // 通知父组件更新 userInfo
        if (onReset) {
          onReset({
            user_id: result.new_user_id,
            user_name: result.new_user_name || userName.trim(),
            agent_name: result.new_agent_name || agentName.trim()
          })
        }
        
        // 延迟清除成功消息并关闭设置页面
        setTimeout(() => {
          setSuccess('')
          if (onClose) {
            onClose()
          }
        }, 500) // 缩短延迟，快速关闭
      } else {
        setError(result.message || '更新失败')
      }
    } catch (err) {
      console.error('更新名字失败:', err)
      setError(err.response?.data?.detail || '更新失败，请重试')
    } finally {
      setIsSaving(false)
    }
  }

  const handleResetCore = () => {
    // RESET CORE = 清空两个名字的文本输入
    setUserName('')
    setAgentName('')
    setIsEditing(false)
    setError('')
    setSuccess('')
  }

  const content = (
    <div className="settings-view" onClick={(e) => showOverlay && e.stopPropagation()}>
      <div className="settings-inner">
          {/* 右上角关闭按钮 */}
          <button 
            className="settings-close-btn"
            onClick={onClose}
            aria-label="Close"
          >
            <svg fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={1.5}>
              <path strokeLinecap="round" strokeLinejoin="round" d="M6 18L18 6M6 6l12 12" />
            </svg>
          </button>

          <div className="text-center mb-16">
            <h3 className="settings-title">SYSTEM CONFIGURATION</h3>
          </div>

          <div className="settings-content">
            {/* TRAVELER 配置 - 直接可编辑 */}
            <div className="config-item">
              <label className="config-label">TRAVELER</label>
              <div className="settings-input-wrapper">
                <input
                  type="text"
                  value={userName}
                  onChange={(e) => setUserName(e.target.value)}
                  className="settings-input traveler-input"
                  placeholder="N/A"
                  disabled={isSaving}
                  onFocus={() => setIsEditing(true)}
                />
                <div className="settings-input-underline"></div>
              </div>
            </div>

            {/* COMPANION 配置 - 直接可编辑 */}
            <div className="config-item">
              <label className="config-label">COMPANION</label>
              <div className="settings-input-wrapper">
                <input
                  type="text"
                  value={agentName}
                  onChange={(e) => setAgentName(e.target.value)}
                  className="settings-input companion-input"
                  placeholder="N/A"
                  disabled={isSaving}
                  onFocus={() => setIsEditing(true)}
                />
                <div className="settings-input-underline"></div>
              </div>
            </div>
          </div>

          {/* 按钮 - RESET CORE 和 COMMIT */}
          <div className="settings-buttons">
            <button 
              className="settings-reset-core-btn"
              onClick={handleResetCore}
              disabled={isSaving}
            >
              Reset Core
            </button>
            <button 
              className="settings-commit-btn"
              onClick={handleCommit}
              disabled={isSaving || !isEditing || (!userName.trim() || !agentName.trim())}
            >
              {isSaving ? 'SAVING...' : 'Commit'}
            </button>
          </div>

          {/* 错误和成功消息 */}
          {(error || success) && (
            <div className="settings-message-container">
              {error && (
                <div className="settings-message settings-error">{error}</div>
              )}
              {success && (
                <div className="settings-message settings-success">{success}</div>
              )}
            </div>
          )}
      </div>
    </div>
  )

  if (showOverlay) {
    return (
      <div className="settings-overlay" onClick={onClose}>
        {content}
      </div>
    )
  }

  return content
}

export default SettingsView
