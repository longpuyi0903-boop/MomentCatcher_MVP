import { useState, useRef, useEffect, forwardRef, useImperativeHandle } from 'react'
import { chatAPI, startMomentAPI, saveMomentAPI, asrAPI, getAudioBaseURL } from '../services/api'
import { useBackgroundStore } from '../store/backgroundStore'
import BackgroundCarousel from './BackgroundCarousel'
import ParticleBackground from './ParticleBackground'
import StarBackground from './StarBackground'
import { useBGM } from '../hooks/useBGM'
import './ChatInterface.css'

const ChatInterface = forwardRef(({ userInfo, onCapture, isCrystallizing }, ref) => {
  const [messages, setMessages] = useState([])
  
  // 包装setMessages，添加日志追踪（用于调试）
  const setMessagesWithLog = useRef((newMessages, source = 'unknown') => {
    const oldMessages = messages
    const oldAssistant = oldMessages.filter(m => m.role === 'assistant').slice(-1)[0]
    const newAssistant = Array.isArray(newMessages) ? newMessages.filter(m => m.role === 'assistant').slice(-1)[0] : null
    
    // 检查是否是重置（从多条消息变成只有1条assistant消息，且是默认问候语）
    const isReset = oldMessages.length > 1 && 
                    Array.isArray(newMessages) && 
                    newMessages.length === 1 && 
                    newMessages[0].role === 'assistant' &&
                    oldAssistant &&
                    oldAssistant.content !== newMessages[0].content
    
    if (isReset || (source && source.includes('init') && oldMessages.length > 0)) {
      console.error(`🚨 [${source}] 检测到messages被重置！`)
      console.error('   旧messages长度:', oldMessages.length)
      console.error('   新messages长度:', Array.isArray(newMessages) ? newMessages.length : 0)
      console.error('   旧assistant消息:', oldAssistant?.content.substring(0, 50))
      console.error('   新assistant消息:', newAssistant?.content.substring(0, 50))
      console.error('   调用栈:', new Error().stack.split('\n').slice(1, 6).join('\n'))
    }
    
    setMessages(newMessages)
  }).current
  const [inputText, setInputText] = useState('')
  const [isLoading, setIsLoading] = useState(false)
  const [currentMomentId, setCurrentMomentId] = useState(null)
  const [audioUrl, setAudioUrl] = useState(null)
  
  // 背景选择状态（使用全局状态管理）
  const selectedBackground = useBackgroundStore((state) => state.selectedBackground)
  const sessionChoiceMade = useBackgroundStore((state) => state.sessionChoiceMade) // 本轮会话是否已选择过背景（不持久化）
  const sessionUserId = useBackgroundStore((state) => state.sessionUserId) // 当前会话用户ID（不持久化）
  const userBackgrounds = useBackgroundStore((state) => state.userBackgrounds) // 获取所有用户的背景
  const backgroundLoaded = useBackgroundStore((state) => state.backgroundLoaded)
  const particlesInitialized = useBackgroundStore((state) => state.particlesInitialized)
  const setSelectedBackground = useBackgroundStore((state) => state.setSelectedBackground)
  const setCurrentUserId = useBackgroundStore((state) => state.setCurrentUserId)
  const setSessionChoiceMade = useBackgroundStore((state) => state.setSessionChoiceMade)
  const setSessionUserId = useBackgroundStore((state) => state.setSessionUserId)
  
  // 背景选择器显示状态（改为动态计算，不依赖局部状态）
  const [isTransitioning, setIsTransitioning] = useState(false)
  const [uiVisible, setUiVisible] = useState(false)
  // 修复：使用ref来持久化isAppReady状态，避免切换视图时重置
  const isAppReadyRef = useRef(false)
  const [isAppReady, setIsAppReady] = useState(false) // 应用是否准备就绪（背景选择完成后）
  const carouselContainerRef = useRef(null)
  // 流星雨特效状态
  const [isWarping, setIsWarping] = useState(false)
  
  // 核心修复：使用 sessionChoiceMade 来控制是否显示背景选择器
  // sessionChoiceMade 不会被持久化，所以每次刷新页面都会重置为 false
  // 从 Memories 返回时，因为 App 没有刷新，sessionChoiceMade 还是 true，所以不会显示选择器
  const shouldShowSelector = !sessionChoiceMade && messages.length === 0
  
  // 背景图片列表 - 动态加载星体素材文件夹下的所有PNG图片
  // 注意：图片路径需要相对于 public 目录
  const [backgroundImages, setBackgroundImages] = useState([])
  
  useEffect(() => {
    // 动态加载星体素材文件夹下的所有PNG图片
    // 注意：前端无法动态扫描文件夹，需要手动维护此列表
    // 如果添加了新图片，需要在此处更新列表
    const imageFiles = [
      'edmunds.png',
      'jupiter.png',
      'KEPLER-186F.png',
      'mann.png',
      'Miller.png',
      'neptune.png',
      'saturn.png',
      'URANUS.png',
      'venus.png',
    ]
    
    // 构建完整路径
    const images = imageFiles.map(file => `/星体素材/${file}`)
    setBackgroundImages(images)
    console.log('🖼️ 背景图片列表:', images)
  }, [])
  
  // 调试：打印背景状态
  useEffect(() => {
    console.log('🎨 ChatInterface 背景状态:', {
      selectedBackground,
      backgroundLoaded,
      particlesInitialized,
      sessionChoiceMade,
      sessionUserId,
      shouldShowSelector,
      messagesLength: messages.length,
      uiVisible,
      isAppReady,
      hasInitialized: hasInitializedRef.current,
      currentUserId: userInfo?.user_id
    })
  }, [selectedBackground, backgroundLoaded, particlesInitialized, sessionChoiceMade, sessionUserId, shouldShowSelector, messages.length, uiVisible, isAppReady, userInfo?.user_id])
  
  // 5块状态信息
  const [audioStatus, setAudioStatus] = useState('LINK ACTIVE') // RECEIVING / PROCESSING / LINK ACTIVE
  const [emotion, setEmotion] = useState('Neutral') // 情绪状态
  const [lastSpeaker, setLastSpeaker] = useState(null) // 最近说话人
  const [subtitle, setSubtitle] = useState('') // 实时字幕
  const [isScrolling, setIsScrolling] = useState(false) // 是否正在滚动
  const [scrollStyle, setScrollStyle] = useState({}) // 滚动动画样式
  
  // 录音状态
  const [isRecording, setIsRecording] = useState(false) // 是否正在录音
  
  // BGM状态：监听语音播放（audioUrl存在且正在播放）
  const [isVoicePlaying, setIsVoicePlaying] = useState(false)
  
  // BGM管理器
  useBGM(isAppReady, isRecording, isVoicePlaying)
  const [recordingState, setRecordingState] = useState('idle') // idle / recording / processing / error
  const [recordingDuration, setRecordingDuration] = useState(0) // 录音时长（秒）

  const audioRef = useRef(null)
  const subtitleRef = useRef(null) // 字幕容器ref
  const subtitleTextRef = useRef(null) // 字幕文本ref
  const mediaRecorderRef = useRef(null) // MediaRecorder 实例
  const recordingChunksRef = useRef([]) // 录音数据块
  const recordingTimerRef = useRef(null) // 录音时长计时器
  const recordingDurationRef = useRef(0) // 录音时长（ref，避免闭包问题）
  const streamRef = useRef(null) // 音频流
  const lastAssistantMsgRef = useRef(null) // 保存最后一条assistant消息，确保processing期间也能显示
  const lastUserMsgRef = useRef(null) // 保存最后一条user消息，确保processing期间也能显示
  const userInteractedRef = useRef(false) // 【移动端修复】用户交互标记

  // ==========================================
  // 核心修复：使用 sessionUserId（不持久化）来区分新登录和会话内切换
  // ==========================================
  // 设置当前用户ID并恢复背景（用于 Memories 页显示）
  useEffect(() => {
    if (userInfo && userInfo.user_id) {
      // 恢复背景（从 localStorage），但不影响 sessionChoiceMade
      setCurrentUserId(userInfo.user_id)
    }
  }, [userInfo?.user_id, setCurrentUserId])
  
  // 新会话检测逻辑：对比 Store 中的 sessionUserId
  // 只有当 Store 里的会话用户ID 与当前用户ID 不一致时，才视为新会话
  // 刷新页面后 sessionUserId 为 null，会触发重置（满足需求1）
  // 切换页面回来 sessionUserId 仍为当前用户，不会触发重置（满足需求2）
  // 如果已经有背景选择且 sessionUserId 不为 null，说明这是同会话内的名字更新，不应该重置状态
  useEffect(() => {
    if (userInfo && userInfo.user_id) {
      const isNewSession = sessionUserId !== userInfo.user_id
      
      if (isNewSession) {
        // 核心修复：如果 sessionUserId 为 null，说明是刷新页面，应该重置 sessionChoiceMade
        // 只有当 sessionUserId 不为 null 且与当前 user_id 不一致时，才检查是否是名字更新
        if (sessionUserId === null) {
          // 刷新页面：重置所有状态，显示背景选择页
          console.log('🆕 [ChatInterface] 检测到刷新页面，重置 sessionChoiceMade')
          
          // 更新 Store 中的当前会话用户
          setSessionUserId(userInfo.user_id)
          
          // 重置选择状态（确保显示背景选择页）
          setSessionChoiceMade(false)
          
          // 重置 UI 状态
          setMessages([])
          hasInitializedRef.current = false
          isAppReadyRef.current = false
          setIsAppReady(false)
          setUiVisible(false)
        } else {
          // sessionUserId 不为 null，说明是会话内的变化
          // 检查是否已经有背景选择：如果有，说明这是同会话内的名字更新，不应该重置
          const hasBackground = selectedBackground !== null && selectedBackground !== undefined
          
          if (hasBackground) {
            console.log('🔄 [ChatInterface] 检测到 user_id 变化，但已有背景选择，视为同会话内的名字更新，保持状态')
            
            // 迁移背景数据：从旧的 user_id 迁移到新的 user_id
            const oldUserId = sessionUserId
            const newUserId = userInfo.user_id
            if (oldUserId && oldUserId !== newUserId && selectedBackground) {
            console.log(`🔄 [ChatInterface] 迁移背景数据：${oldUserId} -> ${newUserId}`)
            // 将背景数据从旧的 user_id 迁移到新的 user_id
            // 使用 setSelectedBackground 会自动更新 userBackgrounds
            setSelectedBackground(selectedBackground, newUserId)
            
            // 更新问候语：如果当前有问候语消息，重新获取新的问候语
            const updateGreeting = async () => {
              try {
                // 检查是否有问候语消息（第一条 assistant 消息）
                const firstAssistantMsg = messages.find(m => m.role === 'assistant')
                const isGreeting = firstAssistantMsg && firstAssistantMsg.content && (
                  firstAssistantMsg.content.includes('我在呢') || 
                  firstAssistantMsg.content.includes('有什么想说的') ||
                  firstAssistantMsg.content.includes('I\'m here') ||
                  firstAssistantMsg.content.includes('what do you want') ||
                  (firstAssistantMsg.content.includes('Hi') && firstAssistantMsg.content.includes('想聊')) ||
                  firstAssistantMsg.content.includes('嘿') ||
                  firstAssistantMsg.content.includes('今天过得') ||
                  firstAssistantMsg.content.includes('你好') ||
                  firstAssistantMsg.content.includes('Hello')
                )
                
                if (isGreeting && messages.length > 0) {
                  console.log('🔄 [ChatInterface] 检测到问候语，更新为新的名字')
                  // 重新获取新的问候语（这会开始一个新的 moment，但前端的对话历史会保留）
                  const result = await startMomentAPI(newUserId)
                  const newGreetingMsg = { role: 'assistant', content: result.greeting }
                  
                  // 更新消息列表：替换第一条 assistant 消息，保留其他消息
                  setMessages(prevMessages => {
                    const updatedMessages = [...prevMessages]
                    const firstAssistantIndex = updatedMessages.findIndex(m => m.role === 'assistant')
                    if (firstAssistantIndex !== -1) {
                      updatedMessages[firstAssistantIndex] = newGreetingMsg
                      lastAssistantMsgRef.current = newGreetingMsg
                      console.log('✅ [ChatInterface] 问候语已更新:', newGreetingMsg.content)
                    }
                    return updatedMessages
                  })
                  
                  // 更新当前 moment ID（后续对话会使用新的 moment）
                  setCurrentMomentId(result.moment_id)
                  console.log('✅ [ChatInterface] Moment ID 已更新:', result.moment_id)
                } else {
                  console.log('ℹ️ [ChatInterface] 未检测到问候语，跳过更新')
                }
              } catch (error) {
                console.error('❌ 更新问候语失败:', error)
                // 即使失败也不影响其他功能
              }
            }
            
            // 异步更新问候语（不阻塞其他操作）
            updateGreeting()
          } else {
            // 如果没有旧 user_id 或背景已存在，直接更新
            setSelectedBackground(selectedBackground, newUserId)
          }
          
            // 更新 sessionUserId
            setSessionUserId(newUserId)
            // 更新当前用户ID（用于背景恢复）
            setCurrentUserId(newUserId)
          } else {
            // 如果没有背景，说明是新会话，重置状态
            console.log('🆕 [ChatInterface] 检测到新登录用户（会话内切换但无背景），重置 sessionChoiceMade')
        
        // 更新 Store 中的当前会话用户
        setSessionUserId(userInfo.user_id)
        
        // 重置选择状态
        setSessionChoiceMade(false)
        
        // 重置 UI 状态
        setMessages([])
        hasInitializedRef.current = false
        isAppReadyRef.current = false
        setIsAppReady(false)
        setUiVisible(false)
          }
        }
      } else {
        console.log('♻️ [ChatInterface] 检测到同会话返回，保持原有状态')
      }
    }
  }, [userInfo?.user_id, sessionUserId, setSessionChoiceMade, setSessionUserId, selectedBackground, setCurrentUserId])

  // 根据shouldShowSelector动态设置isAppReady和uiVisible
  useEffect(() => {
    if (shouldShowSelector) {
      // 需要显示选择器：确保所有状态都重置
      setIsAppReady(false)
      isAppReadyRef.current = false
      setUiVisible(false)
      // 重置初始化标记，防止之前的初始化影响新会话
      hasInitializedRef.current = false
    } else if (selectedBackground) {
      // 不需要显示选择器，且有背景，显示主UI
      setIsAppReady(true)
      isAppReadyRef.current = true
      setUiVisible(true)
    } else {
      // 既不需要显示选择器，也没有背景：确保状态是false
      setIsAppReady(false)
      isAppReadyRef.current = false
      setUiVisible(false)
    }
  }, [shouldShowSelector, selectedBackground])
  
  // 处理背景选择
  const handleBackgroundSelect = (imagePath) => {
    // 设置选中的背景（关联到当前用户）
    // 这会同时更新内存状态和持久化状态，并自动设置 sessionChoiceMade = true
    if (userInfo && userInfo.user_id) {
      setSelectedBackground(imagePath, userInfo.user_id)
    } else {
      setSelectedBackground(imagePath, null)
    }
    
    // 触发流星雨特效（1:1 复刻参考代码：立即切换到 INITIATING 状态）
    setIsWarping(true)
    setIsTransitioning(true)
    
    // 1:1 复刻参考代码：2.5秒后自动切换到主页面（CONNECTED 状态）
    setTimeout(() => {
      setIsWarping(false)
      setIsTransitioning(false)
      setIsAppReady(true)
      isAppReadyRef.current = true // 持久化标记
      setUiVisible(true)
    }, 2500)
  }
  
  // 初始化时自动开始一个 Moment（只在背景选择完成后执行）
  const hasInitializedRef = useRef(false)
  useEffect(() => {
    if (!userInfo || !userInfo.user_id) {
      return
    }
    
    // 核心修复：如果应该显示选择器，绝对不执行初始化逻辑
    // 这确保在背景选择完成之前，不会设置messages，从而不会影响shouldShowSelector
    if (shouldShowSelector) {
      console.log('⏸️ [初始化] 应该显示背景选择器，跳过初始化')
      hasInitializedRef.current = false // 重置初始化标记
      return
    }
    
    // 如果没有背景，也不执行初始化（等待用户选择）
    if (!selectedBackground) {
      console.log('⏸️ [初始化] 没有背景，跳过初始化')
      hasInitializedRef.current = false
      return
    }
    
    // 如果已经初始化过且背景已选择，直接标记为准备就绪
    if (hasInitializedRef.current && selectedBackground) {
      setIsAppReady(true)
      isAppReadyRef.current = true
      setUiVisible(true)
      return
    }
    
    // 只有在背景加载完成后才初始化聊天
    if (!backgroundLoaded || !particlesInitialized) {
      return
    }
    
    // 如果已经初始化过，不再重复初始化
    if (hasInitializedRef.current) {
      setIsAppReady(true)
      isAppReadyRef.current = true
      setUiVisible(true)
      return
    }
    
    const initiateChat = async () => {
      try {
        setIsLoading(true)
        console.log('🚀 开始初始化聊天，user_id:', userInfo.user_id)
        const result = await startMomentAPI(userInfo.user_id)
        console.log('✅ 初始化成功，完整返回数据:', JSON.stringify(result, null, 2))
        console.log('✅ greeting字段:', result?.greeting)
        console.log('✅ message字段:', result?.message)
        // 如果greeting不存在，使用默认值
        const greeting = result?.greeting || result?.message || '我在呢，有什么想说的吗？'
        console.log('✅ 最终使用的greeting:', greeting)
        const greetingMsg = { role: 'assistant', content: greeting }
        setCurrentMomentId(result.moment_id)
        // 只有在messages为空时才设置初始问候语，避免覆盖已有消息
        // 使用函数式更新，确保获取最新的messages状态
        setMessages(prevMessages => {
          if (prevMessages.length === 0) {
            console.log('✅ 初始化：设置默认问候语')
            lastAssistantMsgRef.current = greetingMsg
            return [greetingMsg]
          } else {
            console.log('⚠️ 初始化：messages不为空，跳过设置默认问候语，保持现有消息')
            return prevMessages
          }
        })
        setLastSpeaker(userInfo.agent_name)
        // 只有在背景加载完成后才显示问候语
        if (backgroundLoaded && particlesInitialized) {
          setSubtitle(result.greeting)
        }
        setEmotion('Neutral')
        setAudioStatus('LINK ACTIVE')
        hasInitializedRef.current = true
        setIsAppReady(true)
        isAppReadyRef.current = true
        setUiVisible(true)
      } catch (error) {
        console.error('❌ Error initiating chat:', error)
        console.error('   错误详情:', error.message)
        console.error('   错误堆栈:', error.stack)
        setAudioStatus('LINK ACTIVE')
        // 即使失败也显示错误消息（但只在messages为空时）
        setMessages(prevMessages => {
          if (prevMessages.length === 0) {
            const errorMsg = { role: 'assistant', content: `初始化失败：${error.message || '请检查后端是否启动（http://localhost:8000）'}` }
            lastAssistantMsgRef.current = errorMsg
            return [errorMsg]
          } else {
            console.log('⚠️ 初始化失败但messages不为空，保持现有消息')
            return prevMessages
          }
        })
        hasInitializedRef.current = true
      } finally {
        setIsLoading(false)
      }
    }
    initiateChat()
  }, [shouldShowSelector, selectedBackground, backgroundLoaded, particlesInitialized, userInfo?.user_id, userInfo?.agent_name])

  // 【移动端修复】标记用户已交互（移动端音频播放需要）
  useEffect(() => {
    const markUserInteraction = () => {
      userInteractedRef.current = true
      console.log('👆 [移动端修复] 用户交互标记已设置')
    }
    
    // 监听任何用户交互（包括点击、触摸、输入等）
    document.addEventListener('touchstart', markUserInteraction, { once: true })
    document.addEventListener('click', markUserInteraction, { once: true })
    document.addEventListener('keydown', markUserInteraction, { once: true })
    
    return () => {
      document.removeEventListener('touchstart', markUserInteraction)
      document.removeEventListener('click', markUserInteraction)
      document.removeEventListener('keydown', markUserInteraction)
    }
  }, [])
  
  // 自动播放音频（每次audioUrl变化时重新加载并播放）
  useEffect(() => {
    if (audioUrl && audioRef.current) {
      // 先停止并重置音频
      audioRef.current.pause()
      audioRef.current.currentTime = 0
      // 清除src，强制重新加载
      audioRef.current.src = ''
      // 设置新的音频源
      audioRef.current.src = audioUrl
      // 重新加载音频源
      audioRef.current.load()
      
      // 【移动端修复】播放音频（移动端需要用户交互）
      const playAudio = () => {
        setIsVoicePlaying(true) // 标记语音开始播放
        const playPromise = audioRef.current.play()
        
        if (playPromise !== undefined) {
          playPromise
            .then(() => {
              console.log('🔊 [移动端修复] 语音播放成功')
            })
            .catch(err => {
              console.error('❌ [移动端修复] 语音播放失败:', err)
              console.error('   错误详情:', err.message)
              setIsVoicePlaying(false)
              
              // 【移动端修复】如果自动播放失败，显示提示
              if (/Mobile|Android|iPhone|iPad/i.test(navigator.userAgent)) {
                console.warn('⚠️ [移动端修复] 移动端自动播放被阻止，可能需要用户交互')
                // 可以在这里显示一个播放按钮，让用户手动播放
              }
            })
        }
      }
      
      // 移动端：如果用户已交互，立即播放；否则等待用户交互
      if (userInteractedRef.current) {
        playAudio()
      } else {
        // 等待用户交互后再播放
        const handleInteraction = () => {
          userInteractedRef.current = true
          playAudio()
          document.removeEventListener('touchstart', handleInteraction)
          document.removeEventListener('click', handleInteraction)
        }
        document.addEventListener('touchstart', handleInteraction, { once: true })
        document.addEventListener('click', handleInteraction, { once: true })
      }
    } else {
      setIsVoicePlaying(false)
    }
  }, [audioUrl])
  

  // 更新最后说话人，并确保lastAssistantMsgRef始终保存最后一条assistant消息
  useEffect(() => {
    // 添加详细日志追踪messages的变化
    if (process.env.NODE_ENV === 'development') {
      console.log('📊 [useEffect-messages] messages变化:', {
        length: messages.length,
        messages: messages.map(m => ({ role: m.role, content: m.content.substring(0, 30) })),
        lastAssistantInRef: lastAssistantMsgRef.current?.content.substring(0, 30),
        audioStatus: audioStatus
      })
    }
    
    if (messages.length > 0) {
      const lastMessage = messages[messages.length - 1]
      setLastSpeaker(lastMessage.role === 'user' ? userInfo.user_name : userInfo.agent_name)
      // 不更新subtitle，避免闪烁
      // setSubtitle(lastMessage.content)
      
      // 确保lastAssistantMsgRef始终保存最后一条assistant消息
      // 但只有在messages中有assistant消息时才更新ref，避免在processing期间被重置
      const latestAssistantMsg = messages.filter(m => m.role === 'assistant').slice(-1)[0]
      if (latestAssistantMsg) {
        // 检查messages数组是否被重置（只有1条assistant消息，且ref中已经有其他消息）
        // 如果messages数组只有1条消息且是assistant消息，且ref中已经有消息，可能是被重置了
        const isReset = messages.length === 1 && 
                        messages[0].role === 'assistant' && 
                        lastAssistantMsgRef.current &&
                        lastAssistantMsgRef.current.content !== latestAssistantMsg.content
        
        // 只有在不是重置的情况下才更新ref
        // 这样可以防止在processing期间messages被重置为默认问候语时覆盖ref
        if (!isReset) {
          lastAssistantMsgRef.current = latestAssistantMsg
          if (process.env.NODE_ENV === 'development') {
            console.log('✅ [useEffect] 更新lastAssistantMsgRef:', latestAssistantMsg.content.substring(0, 50))
          }
        } else {
          console.error('🚨 [useEffect] 检测到messages被重置！保持显示ref中的消息')
          console.error('   ref中的消息:', lastAssistantMsgRef.current.content.substring(0, 50))
          console.error('   messages中的消息:', messages[0].content.substring(0, 50))
          console.error('   audioStatus:', audioStatus)
        }
      }
      
      // 确保lastUserMsgRef始终保存最后一条user消息
      const latestUserMsg = messages.filter(m => m.role === 'user').slice(-1)[0]
      if (latestUserMsg) {
        lastUserMsgRef.current = latestUserMsg
      }
    } else {
      // messages为空时，也记录日志
      if (process.env.NODE_ENV === 'development') {
        console.log('⚠️ [useEffect] messages为空，但ref中有消息:', lastAssistantMsgRef.current?.content.substring(0, 50))
      }
    }
  }, [messages, userInfo, audioStatus])

  // 字幕滚动效果 - 从一开始就匀速向上滚动
  useEffect(() => {
    if (!subtitle || !subtitleRef.current || !subtitleTextRef.current) {
      setIsScrolling(false)
      setScrollStyle({})
      return
    }

    // 重置滚动状态
    setIsScrolling(false)
    setScrollStyle({})

    // 等待DOM更新后计算高度并立即开始滚动
    const timer = setTimeout(() => {
      const container = subtitleRef.current
      const textElement = subtitleTextRef.current
      
      if (!container || !textElement) return
      
      const containerHeight = container.clientHeight
      const textHeight = textElement.scrollHeight
      
      // 无论内容多少，都启动滚动效果
      // 如果文本高度小于等于容器高度，让文本从底部滚动到顶部（至少滚动文本高度）
      // 如果文本高度大于容器高度，滚动到完全显示
      const lineHeight = parseFloat(getComputedStyle(textElement).lineHeight) || 1.5 * parseFloat(getComputedStyle(textElement).fontSize)
      const scrollDistance = textHeight > containerHeight 
        ? textHeight - containerHeight  // 内容多时，滚动超出部分
        : Math.max(textHeight, containerHeight * 0.3)  // 内容少时，至少滚动文本高度或容器的30%
      
      // 计算滚动时间：根据文本长度动态计算，保持匀速
      // 每行约1.5秒，最少2秒，最多20秒
      const estimatedLines = Math.ceil(textHeight / lineHeight)
      const duration = Math.min(Math.max(estimatedLines * 1.5, 2), 20)
      
      setScrollStyle({
        '--scroll-distance': `-${scrollDistance}px`,
        '--scroll-duration': `${duration}s`
      })
      
      // 立即启动滚动，不延迟
      setIsScrolling(true)
    }, 50) // 减少延迟，快速启动

    return () => clearTimeout(timer)
  }, [subtitle])

  const handleStartMoment = async () => {
    try {
      setIsLoading(true)
      const result = await startMomentAPI(userInfo.user_id)
      const greetingMsg = { role: 'assistant', content: result.greeting }
      // 更新ref，保存默认问候语
      lastAssistantMsgRef.current = greetingMsg
      // 清空user消息ref
      lastUserMsgRef.current = null
      setCurrentMomentId(result.moment_id)
      // 只设置默认问候语，user消息清空
      setMessages([greetingMsg])
      setSubtitle('') // 清除字幕
      setLastSpeaker(null) // 清除说话人
      setEmotion('Neutral')
      setAudioStatus('LINK ACTIVE')
    } catch (error) {
      console.error('Start moment error:', error)
      setAudioStatus('LINK ACTIVE')
    } finally {
      setIsLoading(false)
    }
  }

  const handleSendMessage = async () => {
    if (!inputText.trim() || isLoading) return

    const userMessage = inputText.trim()
    setInputText('')
    setIsLoading(true)
    
    // 先清除旧音频，避免播放旧语音
    setAudioUrl(null)
    if (audioRef.current) {
      audioRef.current.pause()
      audioRef.current.src = ''
    }
    
    setAudioStatus('RECEIVING...')

    // 添加用户消息到界面（不更新subtitle，避免闪烁）
    const userMsg = { role: 'user', content: userMessage }
    const newMessages = [...messages, userMsg]
    // 更新user消息ref
    lastUserMsgRef.current = userMsg
    setMessages(newMessages)
    setLastSpeaker(userInfo.user_name)
    // 不更新subtitle，避免闪烁

    // 保持RECEIVING状态一小段时间，让用户看到
    await new Promise(resolve => setTimeout(resolve, 300))

    try {
      // 如果没有活跃的 Moment，自动开始一个（但不重置消息）
      if (!currentMomentId) {
        const momentResult = await startMomentAPI(userInfo.user_id)
        setCurrentMomentId(momentResult.moment_id)
        // 注意：不在这里重置 messages，因为用户消息已经添加了
        // 只在初始化时设置 greeting，后续保持现有消息
      }

      setAudioStatus('PROCESSING...')

      // 【移动端修复】发送消息前标记用户交互（确保后续音频可以播放）
      userInteractedRef.current = true
      
      // 发送消息（使用最新的消息列表）
      const result = await chatAPI(userInfo.user_id, userMessage, newMessages)
      
      // 添加 Agent 回复（不更新subtitle，避免闪烁）
      const assistantMsg = { role: 'assistant', content: result.reply }
      setMessages([...newMessages, assistantMsg])
      lastAssistantMsgRef.current = assistantMsg // 保存最后一条assistant消息到ref
      setLastSpeaker(userInfo.agent_name)
      // 不更新subtitle，避免闪烁
      
      // 更新情绪（标准化为英文）
      setEmotion(normalizeEmotion(result.emotion))
      
      // 更新音频（添加时间戳防止缓存）
      if (result.audio_path) {
        const basePath = result.audio_path.startsWith('http') 
          ? result.audio_path 
              : `${getAudioBaseURL()}${result.audio_path}`
        // 添加时间戳强制刷新，避免缓存旧音频
        const audioPath = `${basePath}?t=${Date.now()}`
        // 先清除旧音频URL，确保重新加载
        setAudioUrl(null)
        // 使用setTimeout确保清除后再设置新URL
        setTimeout(() => {
          setAudioUrl(audioPath)
        }, 100)
      }

      setAudioStatus('LINK ACTIVE')
      setCurrentMomentId(result.moment_id)
    } catch (error) {
      console.error('Send message error:', error)
      setAudioStatus('LINK ACTIVE')
      // 不要恢复消息状态，保留用户消息（用户消息已经在第187行添加了）
      // setMessages(messages) // 注释掉，避免消息消失
      setSubtitle('')
      // 显示错误提示
      alert('发送消息失败：' + (error.message || '请重试'))
    } finally {
      setIsLoading(false)
    }
  }

  const handleSaveMoment = () => {
    // 只触发Capture弹窗，不立即保存
    // 实际的保存操作在点击CRYSTALLIZE后执行
    if (!currentMomentId) {
      console.warn('No active moment to save')
      return
    }
    
    // 触发Capture弹窗（传递currentMomentId用于后续保存）
    if (onCapture) {
      onCapture({ momentId: currentMomentId })
    }
  }
  
  const handleCrystallizeMoment = async () => {
    // 点击CRYSTALLIZE后执行实际的保存操作
    if (!currentMomentId) {
      return
    }

    try {
      setIsLoading(true)
      const result = await saveMomentAPI(userInfo.user_id)
      
      // 保存完成后才清除状态（但保留字幕直到Moment Card显示）
      // 字幕会在Moment Card显示后由父组件控制清除
      
      // 返回Moment Card数据
      return result.card
    } catch (error) {
      console.error('Save moment error:', error)
      return null
    } finally {
      setIsLoading(false)
    }
  }
  
  const handleClearChat = async () => {
    // 清除聊天状态（在Moment Card显示后调用）
    // 和点击"开始新 Moment"一样的效果：显示默认问候语，user端清空
    try {
      setIsLoading(true)
      const result = await startMomentAPI(userInfo.user_id)
      const greetingMsg = { role: 'assistant', content: result.greeting }
      // 更新ref，保存默认问候语
      lastAssistantMsgRef.current = greetingMsg
      // 清空user消息ref
      lastUserMsgRef.current = null
      setCurrentMomentId(result.moment_id)
      // 只设置默认问候语，user消息清空
      setMessages([greetingMsg])
      setSubtitle('') // 清除字幕
      setLastSpeaker(null) // 清除说话人
      setEmotion('Neutral')
      setAudioStatus('LINK ACTIVE')
    } catch (error) {
      console.error('Clear chat error:', error)
      setAudioStatus('LINK ACTIVE')
      // 即使失败也清空messages
      setMessages([])
      setCurrentMomentId(null)
    } finally {
      setIsLoading(false)
    }
  }

  // ============================================================
  // 录音功能（ASR）
  // ============================================================

  // 将音频 Blob 转换为 WAV 格式（用于 ASR API 兼容性）
  const convertToWav = async (audioBlob) => {
    return new Promise((resolve, reject) => {
      const audioContext = new (window.AudioContext || window.webkitAudioContext)()
      const fileReader = new FileReader()
      
      fileReader.onload = async (e) => {
        try {
          // 解码音频数据
          const audioBuffer = await audioContext.decodeAudioData(e.target.result)
          
          // 转换为 WAV
          const wavBuffer = audioBufferToWav(audioBuffer)
          const wavBlob = new Blob([wavBuffer], { type: 'audio/wav' })
          
          resolve(wavBlob)
        } catch (error) {
          console.error('格式转换失败:', error)
          reject(error)
        } finally {
          audioContext.close()
        }
      }
      
      fileReader.onerror = reject
      fileReader.readAsArrayBuffer(audioBlob)
    })
  }

  // 将 AudioBuffer 转换为 WAV 格式的 ArrayBuffer
  const audioBufferToWav = (buffer) => {
    const length = buffer.length
    const numberOfChannels = buffer.numberOfChannels
    const sampleRate = buffer.sampleRate
    const arrayBuffer = new ArrayBuffer(44 + length * numberOfChannels * 2)
    const view = new DataView(arrayBuffer)
    
    // WAV 文件头
    const writeString = (offset, string) => {
      for (let i = 0; i < string.length; i++) {
        view.setUint8(offset + i, string.charCodeAt(i))
      }
    }
    
    writeString(0, 'RIFF')
    view.setUint32(4, 36 + length * numberOfChannels * 2, true)
    writeString(8, 'WAVE')
    writeString(12, 'fmt ')
    view.setUint32(16, 16, true)
    view.setUint16(20, 1, true)
    view.setUint16(22, numberOfChannels, true)
    view.setUint32(24, sampleRate, true)
    view.setUint32(28, sampleRate * numberOfChannels * 2, true)
    view.setUint16(32, numberOfChannels * 2, true)
    view.setUint16(34, 16, true)
    writeString(36, 'data')
    view.setUint32(40, length * numberOfChannels * 2, true)
    
    // 写入音频数据
    let offset = 44
    for (let i = 0; i < length; i++) {
      for (let channel = 0; channel < numberOfChannels; channel++) {
        const sample = Math.max(-1, Math.min(1, buffer.getChannelData(channel)[i]))
        view.setInt16(offset, sample < 0 ? sample * 0x8000 : sample * 0x7FFF, true)
        offset += 2
      }
    }
    
    return arrayBuffer
  }

  // 清理录音资源
  const cleanupRecording = () => {
    if (streamRef.current) {
      streamRef.current.getTracks().forEach(track => track.stop())
      streamRef.current = null
    }
    if (recordingTimerRef.current) {
      clearInterval(recordingTimerRef.current)
      recordingTimerRef.current = null
    }
    recordingChunksRef.current = []
    recordingDurationRef.current = 0
    setRecordingDuration(0)
  }

  // 开始录音
  const handleStartRecording = async () => {
    try {
      // 请求麦克风权限
      const stream = await navigator.mediaDevices.getUserMedia({ 
        audio: {
          channelCount: 1, // 单声道
          sampleRate: 16000, // 16kHz，ASR 推荐
          echoCancellation: true,
          noiseSuppression: true,
        } 
      })
      
      streamRef.current = stream
      
      // 【测试优化】优先使用webm格式（浏览器原生支持，无需转换，速度更快）
      // 后端ASR支持webm格式，无需前端转换
      let mimeType = 'audio/webm;codecs=opus'
      if (MediaRecorder.isTypeSupported('audio/webm;codecs=opus')) {
        mimeType = 'audio/webm;codecs=opus'
      } else if (MediaRecorder.isTypeSupported('audio/webm')) {
        mimeType = 'audio/webm'
      } else if (MediaRecorder.isTypeSupported('audio/mp4')) {
        mimeType = 'audio/mp4'
      } else if (MediaRecorder.isTypeSupported('audio/wav')) {
        mimeType = 'audio/wav'
      }
      
      // 【测试优化】降低比特率，减少文件大小，提升上传速度
      const mediaRecorder = new MediaRecorder(stream, {
        mimeType: mimeType,
        audioBitsPerSecond: 64000, // 64kbps（降低一半，减少文件大小）
      })
      
      mediaRecorderRef.current = mediaRecorder
      recordingChunksRef.current = []
      
      // 监听数据可用事件
      mediaRecorder.ondataavailable = (event) => {
        if (event.data.size > 0) {
          recordingChunksRef.current.push(event.data)
        }
      }
      
      // 监听录音停止事件
      mediaRecorder.onstop = async () => {
        // 创建音频 Blob
        const audioBlob = new Blob(recordingChunksRef.current, { type: mimeType })
        
        // 先保存录音时长（在清理之前，使用 ref 获取最新值）
        const finalDuration = recordingDurationRef.current
        
        // 清理资源
        cleanupRecording()
        
        // 【测试优化】跳过格式转换，直接使用原始格式上传（大幅提升速度）
        // 后端ASR引擎支持webm/mp4格式，无需前端转换
        let processedBlob = audioBlob
        console.log('⚡ [测试优化] 跳过格式转换，直接使用原始格式:', {
          格式: mimeType,
          大小: audioBlob.size,
          时长: finalDuration + '秒',
          注意: '如果看到"格式转换成功"日志，说明浏览器缓存了旧代码，请强制刷新（Ctrl+Shift+R）'
        })
        
        // 上传并识别（传递录音时长）
        await handleProcessRecording(processedBlob, finalDuration)
      }
      
      // 监听错误事件
      mediaRecorder.onerror = (event) => {
        console.error('MediaRecorder error:', event)
        setRecordingState('error')
        cleanupRecording()
      }
      
      // 【测试优化】增加数据收集频率，减少延迟（每500ms收集一次）
      mediaRecorder.start(500) // 每500ms收集一次数据，减少延迟
      setIsRecording(true)
      setRecordingState('recording')
      setAudioStatus('RECEIVING...')
      
      // 开始计时
      setRecordingDuration(0)
      recordingDurationRef.current = 0
      recordingTimerRef.current = setInterval(() => {
        recordingDurationRef.current += 1
        setRecordingDuration(recordingDurationRef.current)
        // 最长60秒自动停止
        if (recordingDurationRef.current >= 60) {
          handleStopRecording()
        }
      }, 1000)
      
    } catch (error) {
      console.error('录音启动失败:', error)
      setRecordingState('error')
      cleanupRecording()
      
      // 友好的错误提示
      if (error.name === 'NotAllowedError' || error.name === 'PermissionDeniedError') {
        alert('需要麦克风权限才能录音。请在浏览器设置中允许麦克风访问。')
      } else if (error.name === 'NotFoundError' || error.name === 'DevicesNotFoundError') {
        alert('未检测到麦克风设备。请检查设备连接。')
      } else {
        alert('录音启动失败：' + error.message)
      }
    }
  }

  // 停止录音
  const handleStopRecording = () => {
    if (mediaRecorderRef.current && isRecording) {
      mediaRecorderRef.current.stop()
      setIsRecording(false)
      setRecordingState('processing')
      setAudioStatus('PROCESSING...')
    }
  }

  // 处理录音并上传识别
  const handleProcessRecording = async (audioBlob, duration = 0) => {
    const startTime = Date.now() // 【测试优化】性能计时
    try {
      setRecordingState('processing')
      setAudioStatus('PROCESSING...')
      
      // 【测试优化】降低检查阈值，提高兼容性
      // 检查录音时长（至少0.3秒，降低阈值）
      if (duration < 0.3) {
        throw new Error('录音时间太短，请至少录音0.3秒')
      }
      
      // 检查音频大小（降低阈值：至少256字节，提高兼容性）
      if (audioBlob.size < 256) {
        console.error('❌ 音频数据太小:', {
          大小: audioBlob.size,
          时长: duration,
          类型: audioBlob.type
        })
        throw new Error('录音数据太小，可能没有捕获到有效音频')
      }
      
      console.log('✅ 音频数据检查通过:', {
        大小: audioBlob.size,
        时长: duration + '秒',
        类型: audioBlob.type,
        文件大小KB: (audioBlob.size / 1024).toFixed(2)
      })
      
      // 根据实际格式确定文件扩展名
      let fileExtension = '.wav'
      let fileName = 'recording.wav'
      
      if (audioBlob.type.includes('webm')) {
        fileExtension = '.webm'
        fileName = 'recording.webm'
      } else if (audioBlob.type.includes('mp4')) {
        fileExtension = '.mp4'
        fileName = 'recording.m4a'
      }
      
      // 创建 File 对象（ASR API 需要 File 对象）
      const audioFile = new File([audioBlob], fileName, { type: audioBlob.type })
      
      const uploadStartTime = Date.now() // 【测试优化】上传计时
      console.log('📤 [测试优化] 开始上传音频文件:', {
        name: fileName,
        type: audioBlob.type,
        size: audioBlob.size,
        sizeKB: (audioBlob.size / 1024).toFixed(2),
        duration: duration + '秒'
      })
      
      // 调用 ASR API
      const result = await asrAPI(audioFile)
      const uploadTime = Date.now() - uploadStartTime // 【测试优化】上传耗时
      
      console.log('📥 [测试优化] ASR API 响应:', result)
      console.log('⏱️ [测试优化] 上传+识别总耗时:', uploadTime + 'ms', `(${(uploadTime/1000).toFixed(2)}秒)`)
      
      // 如果失败，打印详细信息
      if (!result || !result.success) {
        console.error('❌ ASR 识别失败详情:', {
          success: result?.success,
          message: result?.message,
          text: result?.text
        })
      }
      
      if (result && result.text && result.text.trim()) {
        const recognizedText = result.text.trim()
        
        // 语音识别后直接发送，无需文本框确认
        // 1. 将识别文本直接添加到消息列表（用户消息）
        const userMsg = { role: 'user', content: recognizedText }
        const newMessages = [...messages, userMsg]
        // 更新user消息ref
        lastUserMsgRef.current = userMsg
        setMessages(newMessages)
        setLastSpeaker(userInfo.user_name)
        // 不更新subtitle，避免闪烁
        
        setRecordingState('idle')
        setAudioStatus('PROCESSING...')
        
        // 2. 自动触发 AI 回复流程（调用 chatAPI）
        try {
          // 如果没有活跃的 Moment，自动开始一个（但不重置消息）
          if (!currentMomentId) {
            const momentResult = await startMomentAPI(userInfo.user_id)
            setCurrentMomentId(momentResult.moment_id)
            // 注意：不在这里重置 messages，因为用户消息已经添加了
            // 只在初始化时设置 greeting，后续保持现有消息
          }
          
          // 【移动端修复】发送消息前标记用户交互（确保后续音频可以播放）
          userInteractedRef.current = true
          
          // 发送消息（使用最新的消息列表）
          const chatResult = await chatAPI(userInfo.user_id, recognizedText, newMessages)
          
          // 3. AI 回复也自动添加到消息列表（AI 消息）
          const assistantMsg = { role: 'assistant', content: chatResult.reply }
          setMessages([...newMessages, assistantMsg])
          lastAssistantMsgRef.current = assistantMsg // 保存最后一条assistant消息到ref
          setLastSpeaker(userInfo.agent_name)
          // 不更新subtitle，避免闪烁
          
          // 更新情绪（标准化为英文）
          setEmotion(normalizeEmotion(chatResult.emotion))
          
          // 更新音频（添加时间戳防止缓存）
          console.log('🔊 [测试优化] chatResult音频信息:', {
            audio_path: chatResult.audio_path,
            has_audio: !!chatResult.audio_path
          })
          if (chatResult.audio_path) {
            const basePath = chatResult.audio_path.startsWith('http') 
              ? chatResult.audio_path 
              : `${getAudioBaseURL()}${chatResult.audio_path}`
            const audioPath = `${basePath}?t=${Date.now()}`
            console.log('🔊 [测试优化] 设置音频URL:', audioPath)
            setAudioUrl(null)
            setTimeout(() => {
              setAudioUrl(audioPath)
            }, 100)
          } else {
            console.warn('⚠️ [测试优化] chatResult中没有audio_path字段')
          }
          
          setAudioStatus('LINK ACTIVE')
          setCurrentMomentId(chatResult.moment_id)
        } catch (error) {
          console.error('发送消息失败:', error)
          setAudioStatus('LINK ACTIVE')
          alert('发送消息失败：' + (error.message || '请重试'))
        }
      } else {
        // 检查是否有错误信息
        const errorMsg = result?.message || '识别结果为空'
        console.error('ASR 识别失败:', result)
        throw new Error(errorMsg)
      }
      
    } catch (error) {
      console.error('ASR 识别失败:', error)
      setRecordingState('error')
      setAudioStatus('LINK ACTIVE')
      alert('语音识别失败：' + (error.message || '请重试'))
    }
  }

  // 组件卸载时清理录音资源
  useEffect(() => {
    return () => {
      cleanupRecording()
    }
  }, [])

  // 暴露方法给父组件（包括录音控制方法和isAppReady状态）
  useImperativeHandle(ref, () => ({
    handleSaveMoment,
    handleCrystallizeMoment,
    handleClearChat,
    handleStartRecording,
    handleStopRecording,
    currentMomentId,
    isRecording,
    recordingState,
    isAppReady, // 暴露isAppReady状态，父组件可据此隐藏主按钮
    isWarping // 暴露isWarping状态，父组件可据此在流星雨期间隐藏按钮
  }), [currentMomentId, userInfo.user_id, onCapture, isRecording, recordingState, isAppReady, isWarping])

  // 情绪映射：将中文或小写英文转换为标准英文
  const normalizeEmotion = (emotion) => {
    if (!emotion) return 'Neutral'
    
    const emotionLower = emotion.toLowerCase()
    const emotionMap = {
      // 英文小写
      'joy': 'Joy',
      'sadness': 'Sadness',
      'anger': 'Anger',
      'fear': 'Fear',
      'love': 'Love',
      'surprise': 'Surprise',
      'neutral': 'Neutral',
      'frustration': 'Frustration',
      'embarrassment': 'Embarrassment',
      'shame': 'Shame',
      'awkward': 'Awkward',
      // 中文映射
      '开心': 'Joy',
      '喜悦': 'Joy',
      '兴奋': 'Joy',
      '悲伤': 'Sadness',
      '失落': 'Sadness',
      '难过': 'Sadness',
      '生气': 'Anger',
      '愤怒': 'Anger',
      '激动': 'Anger',
      '恐惧': 'Fear',
      '担心': 'Fear',
      '焦虑': 'Fear',
      '爱': 'Love',
      '温暖': 'Love',
      '感动': 'Love',
      '惊讶': 'Surprise',
      '意外': 'Surprise',
      '平静': 'Neutral',
      '中性': 'Neutral',
      '正常': 'Neutral',
    }
    return emotionMap[emotionLower] || 'Neutral'
  }

  // 获取情绪颜色
  const getEmotionColor = (emotion) => {
    const normalizedEmotion = normalizeEmotion(emotion)
    const emotionMap = {
      'Joy': 'var(--emotion-joy)',
      'Sadness': 'var(--emotion-sadness)',
      'Anger': 'var(--emotion-anger)',
      'Fear': 'var(--emotion-fear)',
      'Love': 'var(--emotion-love)',
      'Surprise': 'var(--emotion-surprise)',
      'Neutral': 'var(--emotion-neutral)',
      'Frustration': 'var(--emotion-anger)',
      'Embarrassment': 'var(--emotion-sadness)',
      'Shame': 'var(--emotion-sadness)',
      'Awkward': 'var(--emotion-neutral)',
    }
    return emotionMap[normalizedEmotion] || emotionMap['Neutral']
  }

  console.log('🎬 [ChatInterface] 渲染决策:', {
    shouldShowSelector,
    isAppReady,
    selectedBackground,
    sessionChoiceMade,
    messagesLength: messages.length
  })

  // 核心逻辑：互斥显示 - 要么显示选择器，要么显示主UI
  // 修复：使用动态计算的shouldShowSelector，不依赖局部状态
  if (shouldShowSelector || isWarping) {
    return (
      <div className="chat-interface">
        {/* 动态星场背景（带流星雨特效）- 1:1 复刻参考代码 */}
        <StarBackground fast={isWarping} />
        
        {/* 背景选择器（3D传送带）- 选择阶段只显示这个 */}
        {!isWarping && (
        <div ref={carouselContainerRef} className="background-carousel-wrapper">
          <BackgroundCarousel 
            images={backgroundImages}
            onSelect={handleBackgroundSelect}
          />
        </div>
        )}
        
        {/* 流星雨特效期间的提示文字 */}
        {isWarping && (
          <div className="warping-overlay">
            <h2 className="warping-text">Initiating Quantum Jump</h2>
            <div className="warping-line">
              <div className="warping-progress"></div>
            </div>
          </div>
        )}
      </div>
    )
  }

  // 主UI内容（背景选择完成后才显示）
  return (
    <div className="chat-interface">
      {/* 动态星场背景 - 1:1 复刻参考代码 */}
      <StarBackground fast={false} />
      
      {/* 粒子背景（如果已选择背景） */}
      {selectedBackground && (
        <ParticleBackground imagePath={selectedBackground} />
      )}
      
      {/* 主UI内容（在背景加载完成后渐显）- 1:1 复刻参考代码入场效果 */}
      <div 
        className={`chat-interface-content ${uiVisible ? 'fade-in-chat' : ''}`}
        style={{
          width: '100%',
          height: '100%'
        }}
      >
      {/* 5块状态信息（从上到下垂直分布） */}
      
      {/* 1. 音频处理状态（顶部） */}
      <div className="status-block status-audio">
        <div className={`status-badge ${audioStatus.toLowerCase().replace(' ', '-')}`}>
          {audioStatus}
        </div>
      </div>

      {/* 2. 情绪状态（第二层） */}
      <div className="status-block status-emotion">
        <div 
          className="emotion-text"
          style={{ color: getEmotionColor(emotion) }}
        >
          {normalizeEmotion(emotion)}
        </div>
      </div>

      {/* 3. 最近说话人（第三层） */}
      {lastSpeaker && (
        <div className="status-block status-speaker">
          <div className="speaker-text">{lastSpeaker.toUpperCase()}</div>
        </div>
      )}

      {/* 对话区域容器 - 填充剩余空间，高度由布局计算 */}
      <div className="voice-conversation-area">
        {(() => {
          // 只显示每一方最新的那句话
          const latestUserMsg = messages.filter(m => m.role === 'user').slice(-1)[0]
          const latestAssistantMsg = messages.filter(m => m.role === 'assistant').slice(-1)[0]
          
          // 检查是否是默认问候语
          const isDefaultGreeting = latestAssistantMsg && latestAssistantMsg.content && (
            latestAssistantMsg.content.includes('我在呢') || 
            latestAssistantMsg.content.includes('有什么想说的') ||
            latestAssistantMsg.content.includes('I\'m here') ||
            latestAssistantMsg.content.includes('what do you want') ||
            latestAssistantMsg.content.includes('Hi') && latestAssistantMsg.content.includes('想聊')
          )
          
          // 检查是否是重置情况：
          // 1. messages只有1条assistant消息，且ref中已经有其他消息
          // 2. 或者在processing期间，最新的assistant消息是默认问候语，且ref中有其他消息
          const isProcessing = audioStatus === 'PROCESSING...' || audioStatus === 'PROCESSING'
          const isReset = (messages.length === 1 && 
                          messages[0].role === 'assistant' && 
                          lastAssistantMsgRef.current &&
                          lastAssistantMsgRef.current.content !== messages[0].content) ||
                         (isProcessing && 
                          isDefaultGreeting && 
                          lastAssistantMsgRef.current &&
                          lastAssistantMsgRef.current.content !== latestAssistantMsg.content)
          
          // 调试日志
          if (isReset) {
            console.log('⚠️ [渲染] 检测到messages被重置为默认问候语！')
            console.log('   audioStatus:', audioStatus)
            console.log('   messages长度:', messages.length)
            console.log('   messages内容:', messages.map(m => `${m.role}: ${m.content.substring(0, 30)}`))
            console.log('   ref中的消息:', lastAssistantMsgRef.current.content.substring(0, 50))
            console.log('   保持显示ref中的消息')
          }
          
          // 确定显示的assistant消息：
          // - 如果在processing期间，且ref中有上一条消息，显示ref中的上一条消息
          // - 否则显示messages中的最新消息或ref中的消息
          let displayAssistantMsg
          if (isProcessing && lastAssistantMsgRef.current) {
            // processing期间，始终显示ref中的上一条消息（确保显示上一条消息，而不是默认问候语）
            displayAssistantMsg = lastAssistantMsgRef.current
          } else if (latestAssistantMsg && !isReset) {
            // 非processing期间，且不是重置，显示messages中的消息
            displayAssistantMsg = latestAssistantMsg
          } else {
            // 其他情况，显示ref中的消息
            displayAssistantMsg = lastAssistantMsgRef.current
          }
          
          // 确定显示的user消息：
          // - 如果在processing期间，且ref中有上一条消息，显示ref中的上一条消息
          // - 否则显示messages中的最新消息或ref中的消息
          let displayUserMsg
          if (isProcessing && lastUserMsgRef.current) {
            // processing期间，始终显示ref中的上一条消息（确保显示上一条消息）
            displayUserMsg = lastUserMsgRef.current
          } else {
            // 非processing期间，显示messages中的最新消息或ref中的消息
            displayUserMsg = latestUserMsg || lastUserMsgRef.current
          }
          
          // 调试日志
          if (!latestAssistantMsg && lastAssistantMsgRef.current) {
            console.log('⚠️ [渲染] messages中没有assistant消息，使用ref中保存的:', lastAssistantMsgRef.current.content.substring(0, 50))
          }
          
          if (displayAssistantMsg && displayAssistantMsg !== latestAssistantMsg && latestAssistantMsg) {
            console.log('⚠️ [渲染] 使用ref中的消息而不是messages中的')
            console.log('   messages中的:', latestAssistantMsg.content.substring(0, 50))
            console.log('   ref中的:', displayAssistantMsg.content.substring(0, 50))
          }
          
          // 使用稳定的key策略：直接基于消息内容生成hash
          // 相同内容总是生成相同的key，避免不必要的重新渲染和闪烁
          const getContentKey = (msg, role) => {
            if (!msg || !msg.content) return `${role}-empty`
            // 使用内容的前30个字符（去除空格）作为key的一部分
            // 这样相同内容总是生成相同的key
            const contentKey = msg.content.substring(0, 30).replace(/\s+/g, '-').substring(0, 25)
            return `${role}-${contentKey}`
          }
          
          const aiKey = getContentKey(displayAssistantMsg, 'assistant')
          const userKey = getContentKey(displayUserMsg, 'user')
          
          return (
            <>
              {/* AI 当前发言 - Viewport，等高自适应 */}
              {displayAssistantMsg && (
                <div key={aiKey} className="voice-ai-speech">
                  <div className="voice-ai-speech-content">
                    <div>
                      {displayAssistantMsg.content}
                    </div>
                  </div>
                </div>
              )}
              
              {/* 用户刚刚说的话 - Viewport，等高自适应 */}
              {displayUserMsg && (
                <div key={userKey} className="voice-user-speech">
                  <div className="voice-user-speech-content">
                    <div>
                      {displayUserMsg.content}
                    </div>
                  </div>
                </div>
              )}
              
              {/* Crystallizing提示（对话区域内） */}
              {isCrystallizing && (
                <div className="status-block status-saving">
                  <div className="saving-text">Crystallizing this moment...</div>
                </div>
              )}
            </>
          )
        })()}
      </div>

      {/* 4. 实时字幕（第四层）- 电影演职人员表式滚动 - 已禁用但保留代码 */}
      {false && subtitle && (
        <div className="status-block status-subtitle">
          <div className="subtitle-container" ref={subtitleRef}>
            <div 
              ref={subtitleTextRef}
              className={`subtitle-text ${isScrolling ? 'scrolling' : ''}`}
              style={scrollStyle}
            >
              {subtitle}
            </div>
          </div>
        </div>
      )}

      {/* 背景选择（左右滑动）- TODO: 实现左右滑动选择预设星图 */}
      <div className="background-selector">
        {/* TODO: 实现左右滑动交互
            - 滑动只改变背景，不影响布局
            - 选中的背景用于该 Moment 的对话背景
            - 保存后成为 Memory Card 的封面
        */}
        {/* 背景已通过 ParticleBackground 组件渲染，不再使用简单的背景图片 */}
      </div>

      {/* 6. 主按钮（第六层，底部）- 在 MainInterface 中实现 */}


      {/* 右侧浮动操作按钮（参考设计：图标形式，hover显示文字） */}
      <div className="floating-side-buttons">
        {/* INITIATE NEW MOMENT 按钮 */}
        <button
          onClick={handleStartMoment}
          disabled={isLoading}
          className="side-action-btn side-action-btn-refresh group"
        >
          <div className="side-button-line side-button-line-top">
            <div className="side-button-dot side-button-dot-top"></div>
          </div>
          <div className="side-button-content">
            <svg 
              width="20" 
              height="20" 
              viewBox="0 0 24 24" 
              fill="none" 
              stroke="currentColor" 
              strokeWidth="2" 
              strokeLinecap="round" 
              strokeLinejoin="round"
              className="side-button-icon"
            >
              <path d="M3 12a9 9 0 0 1 9-9 9.75 9.75 0 0 1 6.74 2.74L21 8" />
              <path d="M21 3v5h-5" />
              <path d="M21 12a9 9 0 0 1-9 9 9.75 9.75 0 0 1-6.74-2.74L3 16" />
              <path d="M3 21v-5h5" />
            </svg>
            <span className="side-button-label side-button-label-refresh">REFRESH</span>
          </div>
        </button>

        {/* ARCHIVE THE MOMENT 按钮 */}
        <button
          onClick={handleSaveMoment}
          disabled={isLoading || !currentMomentId}
          className="side-action-btn group"
          style={{ cursor: (!isLoading && currentMomentId) ? 'pointer' : 'not-allowed' }}
        >
          <div className="side-button-content">
            <span className="side-button-label side-button-label-archive">ARCHIVE</span>
            <svg 
              width="20" 
              height="20" 
              viewBox="0 0 24 24" 
              fill="none" 
              stroke="currentColor" 
              strokeWidth="2" 
              strokeLinecap="round" 
              strokeLinejoin="round"
              className="side-button-icon"
            >
              <rect width="20" height="5" x="2" y="3" rx="1" />
              <path d="M4 8v11a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8" />
              <path d="M10 12h4" />
            </svg>
          </div>
          <div className="side-button-line side-button-line-bottom">
            <div className="side-button-dot side-button-dot-bottom"></div>
          </div>
        </button>
      </div>

      {/* 音频播放器（隐藏，自动播放） */}
      {audioUrl && (
        <audio
          ref={audioRef}
          src={audioUrl}
          onPlay={() => setIsVoicePlaying(true)}
          onPause={() => setIsVoicePlaying(false)}
          onEnded={() => {
            setIsVoicePlaying(false)
            setAudioUrl(null)
          }}
          onError={() => {
            setIsVoicePlaying(false)
            setAudioUrl(null)
          }}
        />
      )}
      </div>
    </div>
  )
})

ChatInterface.displayName = 'ChatInterface'

export default ChatInterface
