import { useState, useRef, useEffect } from 'react'
import ChatInterface from './ChatInterface'
import MemoriesView from './MemoriesView'
import SettingsView from './SettingsView'
import MomentCard from './MomentCard'
import './MainInterface.css'

function MainInterface({ userInfo, onUserInfoUpdate }) {
  const [currentView, setCurrentView] = useState('chat') // 'chat', 'memories', 'settings'
  const [showSettings, setShowSettings] = useState(false)
  const [showCapture, setShowCapture] = useState(false)
  const [captureMomentCard, setCaptureMomentCard] = useState(null)
  const [isCrystallizing, setIsCrystallizing] = useState(false) // 正在封存记忆状态
  const [isRecording, setIsRecording] = useState(false) // 录音状态（从 ChatInterface 获取）
  const [isAppReady, setIsAppReady] = useState(false) // 应用是否准备就绪（背景选择完成后）
  const [isWarping, setIsWarping] = useState(false) // 流星雨特效状态（从 ChatInterface 获取）
  const chatInterfaceRef = useRef(null)
  
  // 定期检查录音状态和应用准备状态（用于更新按钮样式和显示）
  const [shouldAnimateButtons, setShouldAnimateButtons] = useState(false)
  const prevIsWarpingRef = useRef(true) // 初始值设为true，因为开始时可能在流星雨状态
  
  useEffect(() => {
    const interval = setInterval(() => {
      if (chatInterfaceRef.current) {
        const newIsAppReady = chatInterfaceRef.current.isAppReady || false
        const newIsWarping = chatInterfaceRef.current.isWarping || false
        setIsRecording(chatInterfaceRef.current.isRecording || false)
        setIsWarping(newIsWarping)
        
        // 当流星雨结束（从true变为false）且应用准备就绪时，触发按钮动画
        if (prevIsWarpingRef.current && !newIsWarping && newIsAppReady) {
          setShouldAnimateButtons(true)
        }
        
        // 如果重新进入流星雨状态，重置动画
        if (newIsWarping) {
          setShouldAnimateButtons(false)
        }
        
        prevIsWarpingRef.current = newIsWarping
        setIsAppReady(newIsAppReady)
      }
    }, 100) // 每100ms检查一次
    
    return () => clearInterval(interval)
  }, [currentView])

  return (
    <div className="main-interface">

      {/* 主内容区域 */}
      <main className="main-content">
        {currentView === 'chat' && (
          <>
            <ChatInterface 
              ref={chatInterfaceRef}
              userInfo={userInfo}
              isCrystallizing={isCrystallizing}
              onCapture={(data) => {
                // 点击Capture/保存Moment时，先显示Freeze弹窗
                // data可能是{momentId}或{card}
                if (data.momentId) {
                  // 这是触发Capture弹窗
                  setShowCapture(true)
                } else if (data.card) {
                  // 这是保存完成后的card数据
                  setCaptureMomentCard(data.card)
                }
              }}
            />
          </>
        )}
        {currentView === 'memories' && (
          <MemoriesView 
            userInfo={userInfo} 
            onClose={() => setCurrentView('chat')}
          />
        )}
        {currentView === 'settings' && (
          <SettingsView 
            userInfo={userInfo}
            onClose={() => {
              setShowSettings(false)
              setCurrentView('chat')
            }}
            onReset={(updatedUserInfo) => {
              // 名字更新后的回调
              if (updatedUserInfo && onUserInfoUpdate) {
                onUserInfoUpdate(updatedUserInfo)
              } else {
                // 重置功能（清空所有数据）
                if (onUserInfoUpdate) {
                  onUserInfoUpdate(null) // 传递 null 表示重置
                }
              }
            }}
            showOverlay={true}
          />
        )}
      </main>

      {/* 两个主按钮（底部）- 只在chat视图且应用准备就绪时显示，流星雨期间不显示，与主页面内容同步入场动画 */}
      {currentView === 'chat' && isAppReady && !isWarping && (
      <div className="main-buttons fade-in-chat">
        <button
          className={`main-btn ${currentView === 'memories' ? 'active' : ''}`}
          onClick={() => setCurrentView('memories')}
          aria-label="Echoes"
        >
          <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
            <rect x="3" y="3" width="7" height="7"/>
            <rect x="14" y="3" width="7" height="7"/>
            <rect x="3" y="14" width="7" height="7"/>
            <rect x="14" y="14" width="7" height="7"/>
          </svg>
          <span className="btn-label">ECHOES</span>
        </button>

        <button
          className={`main-btn main-btn-center ${currentView === 'chat' ? 'active' : ''} ${isRecording ? 'recording' : ''}`}
          onClick={async () => {
            // 如果不在 chat 视图，先切换视图
            if (currentView !== 'chat') {
              setCurrentView('chat')
              return // 只切换视图，不触发录音
            }
            
            // 在 chat 视图下，根据录音状态切换录音/停止
            if (chatInterfaceRef.current) {
              try {
                if (chatInterfaceRef.current.isRecording) {
                  // 正在录音，停止录音
                  chatInterfaceRef.current.handleStopRecording()
                } else {
                  // 未录音，开始录音
                  chatInterfaceRef.current.handleStartRecording()
                }
              } catch (error) {
                console.error('录音操作失败:', error)
                // 如果录音失败，不影响其他功能
              }
            }
          }}
          aria-label="Record"
        >
          <svg width="28" height="28" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
            <path d="M12 1a3 3 0 0 0-3 3v8a3 3 0 0 0 6 0V4a3 3 0 0 0-3-3z"/>
            <path d="M19 10v2a7 7 0 0 1-14 0v-2"/>
            <line x1="12" y1="19" x2="12" y2="23"/>
            <line x1="8" y1="23" x2="16" y2="23"/>
          </svg>
        </button>

        <button
          className={`main-btn`}
          onClick={() => setShowSettings(true)}
          aria-label="Settings"
        >
          <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
            <path d="M12.22 2h-.44a2 2 0 0 0-2 2v.18a2 2 0 0 1-1 1.73l-.43.25a2 2 0 0 1-2 0l-.15-.08a2 2 0 0 0-2.73.73l-.22.38a2 2 0 0 0 .73 2.73l.15.1a2 2 0 0 1 1 1.72v.51a2 2 0 0 1-1 1.74l-.15.09a2 2 0 0 0-.73 2.73l.22.38a2 2 0 0 0 2.73.73l.15-.08a2 2 0 0 1 2 0l.43.25a2 2 0 0 1 1 1.73V20a2 2 0 0 0 2 2h.44a2 2 0 0 0 2-2v-.18a2 2 0 0 1 1-1.73l.43-.25a2 2 0 0 1 2 0l.15.08a2 2 0 0 0 2.73-.73l.22-.39a2 2 0 0 0-.73-2.73l-.15-.08a2 2 0 0 1-1-1.74v-.5a2 2 0 0 1 1-1.74l.15-.09a2 2 0 0 0 .73-2.73l-.22-.38a2 2 0 0 0-2.73-.73l-.15.08a2 2 0 0 1-2 0l-.43-.25a2 2 0 0 1-1-1.73V4a2 2 0 0 0-2-2z"/>
            <circle cx="12" cy="12" r="3"/>
          </svg>
          <span className="btn-label">SETTINGS</span>
        </button>
      </div>
      )}

      {/* 设置弹窗 */}
      {showSettings && (
        <SettingsView 
          userInfo={userInfo} 
          onClose={() => {
            setShowSettings(false)
            // 确保回到主页面视图
            setCurrentView('chat')
          }}
          onReset={(updatedUserInfo) => {
            // 名字更新后的回调
            if (updatedUserInfo && onUserInfoUpdate) {
              onUserInfoUpdate(updatedUserInfo)
            } else {
              // 重置功能（清空所有数据）
              if (onUserInfoUpdate) {
                onUserInfoUpdate(null) // 传递 null 表示重置
              }
            }
            // 确保关闭设置并回到主页面
            setShowSettings(false)
            setCurrentView('chat')
          }}
          showOverlay={true}
        />
      )}

      {/* Capture 弹窗 - 1:1 复刻参考代码 */}
      {showCapture && (
        <div className="capture-overlay" onClick={() => setShowCapture(false)}>
          <div className="capture-modal" onClick={(e) => e.stopPropagation()}>
            <div className="capture-modal-inner">
              <div className="capture-header">
                <div className="capture-authorizing">// AUTHORIZING QUANTUM INTERLOCK</div>
                <h2 className="capture-title">Freeze this moment?</h2>
              </div>
              <div className="capture-buttons">
                <button 
                  className="capture-btn crystallize"
                  onClick={async () => {
                    // 点击 CRYSTALLIZE：先关闭弹窗，显示封存提示，然后保存Moment
                    setShowCapture(false)
                    setIsCrystallizing(true)
                    
                    // 调用ChatInterface的保存方法
                    if (chatInterfaceRef.current) {
                      const card = await chatInterfaceRef.current.handleCrystallizeMoment()
                      if (card) {
                        setCaptureMomentCard(card)
                        // 保存完成后清除聊天状态
                        setTimeout(() => {
                          if (chatInterfaceRef.current) {
                            chatInterfaceRef.current.handleClearChat()
                          }
                        }, 500)
                      }
                    }
                    
                    // 延迟隐藏封存提示，显示 Moment Card
                    setTimeout(() => {
                      setIsCrystallizing(false)
                    }, 2000)
                  }}
                >
                  CRYSTALLIZE
                </button>
                <button 
                  className="capture-btn fade"
                  onClick={() => {
                    // 点击 FADE：关闭 Capture 弹窗，不显示 Moment Card
                    setShowCapture(false)
                    setCaptureMomentCard(null)
                  }}
                >
                  FADE
                </button>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* Moment Card 显示（点击 CRYSTALLIZE 后显示，封存提示消失后） */}
      {captureMomentCard && !showCapture && !isCrystallizing && (
        <MomentCard 
          card={captureMomentCard} 
          onClose={() => {
            setCaptureMomentCard(null)
            // 清除聊天状态
            if (chatInterfaceRef.current) {
              chatInterfaceRef.current.handleClearChat()
            }
          }}
        />
      )}
    </div>
  )
}

export default MainInterface
