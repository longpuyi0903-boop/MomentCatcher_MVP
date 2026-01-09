import { useEffect, useRef, useState, useCallback } from 'react'

/**
 * BGM管理器Hook
 * 功能：
 * 1. 随机选择并播放BGM
 * 2. 自动循环播放
 * 3. 音量淡入（3秒）
 * 4. 录音/语音播放时音量降到30%
 * 
 * 【移动端修复】
 * - 使用HTML Audio元素代替Web Audio API进行播放（更好的移动端兼容性）
 * - Web Audio API仅用于音量控制
 * - 预加载音频，用户交互后立即播放
 * 
 * 【音量修复】
 * - Audio元素的volume必须设为1，让Web Audio API完全控制音量
 * - 所有音量控制都通过GainNode进行
 */
export const useBGM = (isAppReady, isRecording, isVoicePlaying) => {
  const audioElementRef = useRef(null) // HTML Audio元素（用于播放）
  const audioContextRef = useRef(null) // Web Audio API（仅用于音量控制）
  const gainNodeRef = useRef(null)
  const mediaSourceRef = useRef(null) // MediaElementAudioSourceNode
  const [currentBGM, setCurrentBGM] = useState(null)
  const isPlayingRef = useRef(false)
  const isInitializedRef = useRef(false) // 是否已初始化
  const pendingPlayRef = useRef(false) // 是否有待播放的请求
  const currentVolumeRef = useRef(0) // 当前目标音量（用于追踪）
  
  // BGM文件列表（需要手动维护，添加新BGM时更新此列表）
  const bgmFiles = [
    'Hans Zimmer - Interstellar - Main Theme (Piano Version)  Sheet Music.mp3'
    // 后续添加更多BGM时，在这里添加文件名
  ]
  
  // 音量常量
  const FULL_VOLUME = 0.6 // 正常音量（60%）
  const LOW_VOLUME = 0.18 // 降低后的音量（30% of 60%）
  const FADE_IN_DURATION = 3000 // 淡入时长（3秒）
  
  // 随机选择BGM
  const selectRandomBGM = useCallback(() => {
    if (bgmFiles.length === 0) return null
    const randomIndex = Math.floor(Math.random() * bgmFiles.length)
    return `/bgm/${bgmFiles[randomIndex]}`
  }, [])
  
  // 初始化Audio元素和Web Audio API
  const initAudio = useCallback(() => {
    if (isInitializedRef.current) return
    
    try {
      // 创建HTML Audio元素（移动端兼容性更好）
      if (!audioElementRef.current) {
        const audio = new Audio()
        audio.loop = true
        audio.preload = 'auto'
        // 【音量修复】Audio元素的volume必须设为1
        // 让Web Audio API的GainNode完全控制音量
        audio.volume = 1
        audioElementRef.current = audio
        console.log('🎵 [音量修复] HTML Audio元素创建成功，volume=1')
      }
      
      // 创建Web Audio API（用于精细音量控制）
      if (!audioContextRef.current) {
        audioContextRef.current = new (window.AudioContext || window.webkitAudioContext)()
        gainNodeRef.current = audioContextRef.current.createGain()
        gainNodeRef.current.connect(audioContextRef.current.destination)
        // 【音量修复】GainNode初始音量为0，淡入时会逐渐增加
        gainNodeRef.current.gain.value = 0
        currentVolumeRef.current = 0
        console.log('🎵 [音量修复] Web Audio API初始化成功，gain=0')
      }
      
      // 连接Audio元素到Web Audio API（只连接一次）
      if (!mediaSourceRef.current && audioElementRef.current && audioContextRef.current) {
        try {
          mediaSourceRef.current = audioContextRef.current.createMediaElementSource(audioElementRef.current)
          mediaSourceRef.current.connect(gainNodeRef.current)
          console.log('🎵 [音量修复] Audio元素已连接到Web Audio API')
        } catch (err) {
          // 如果已经连接过，忽略错误
          console.warn('⚠️ [音量修复] Audio元素连接警告（可能已连接）:', err.message)
        }
      }
      
      isInitializedRef.current = true
    } catch (error) {
      console.error('❌ [音量修复] 音频初始化失败:', error)
    }
  }, [])
  
  // 预加载BGM
  const preloadBGM = useCallback((bgmPath) => {
    if (!audioElementRef.current) {
      initAudio()
    }
    
    const encodedPath = encodeURI(bgmPath)
    console.log('🎵 [音量修复] 预加载BGM:', encodedPath)
    
    audioElementRef.current.src = encodedPath
    audioElementRef.current.load()
    
    return new Promise((resolve, reject) => {
      const handleCanPlay = () => {
        console.log('🎵 [音量修复] BGM预加载完成，可以播放')
        audioElementRef.current.removeEventListener('canplaythrough', handleCanPlay)
        audioElementRef.current.removeEventListener('error', handleError)
        resolve()
      }
      
      const handleError = (e) => {
        console.error('❌ [音量修复] BGM预加载失败:', e)
        audioElementRef.current.removeEventListener('canplaythrough', handleCanPlay)
        audioElementRef.current.removeEventListener('error', handleError)
        reject(e)
      }
      
      audioElementRef.current.addEventListener('canplaythrough', handleCanPlay, { once: true })
      audioElementRef.current.addEventListener('error', handleError, { once: true })
      
      // 超时处理
      setTimeout(() => {
        audioElementRef.current.removeEventListener('canplaythrough', handleCanPlay)
        audioElementRef.current.removeEventListener('error', handleError)
        // 即使超时也尝试播放
        resolve()
      }, 10000)
    })
  }, [initAudio])
  
  // 设置音量（统一的音量控制函数）
  const setVolume = useCallback((targetVolume, duration = 0.5) => {
    if (!gainNodeRef.current || !audioContextRef.current) {
      console.warn('⚠️ [音量修复] GainNode未初始化，无法设置音量')
      return
    }
    
    const gainNode = gainNodeRef.current
    const audioContext = audioContextRef.current
    
    // 确保AudioContext在运行
    if (audioContext.state === 'suspended') {
      audioContext.resume()
    }
    
    const currentTime = audioContext.currentTime
    const currentGain = gainNode.gain.value
    
    // 取消之前的调度
    gainNode.gain.cancelScheduledValues(currentTime)
    // 从当前值开始
    gainNode.gain.setValueAtTime(currentGain, currentTime)
    // 平滑过渡到目标音量
    gainNode.gain.linearRampToValueAtTime(targetVolume, currentTime + duration)
    
    currentVolumeRef.current = targetVolume
    console.log(`🎵 [音量修复] 音量调整: ${currentGain.toFixed(2)} -> ${targetVolume.toFixed(2)} (${duration}秒)`)
  }, [])
  
  // 播放BGM（需要在用户交互后调用）
  const playBGM = useCallback(async () => {
    if (isPlayingRef.current) {
      console.log('🎵 [音量修复] BGM已在播放中')
      return
    }
    
    if (!audioElementRef.current) {
      console.warn('⚠️ [音量修复] Audio元素未初始化')
      return
    }
    
    try {
      // 恢复AudioContext（移动端必需）
      if (audioContextRef.current && audioContextRef.current.state === 'suspended') {
        await audioContextRef.current.resume()
        console.log('🎵 [音量修复] AudioContext已恢复，状态:', audioContextRef.current.state)
      }
      
      // 【音量修复】确保Audio元素的volume是1
      audioElementRef.current.volume = 1
      
      // 设置初始音量为0，然后淡入到目标音量
      const gainNode = gainNodeRef.current
      const audioContext = audioContextRef.current
      
      if (gainNode && audioContext) {
        const currentTime = audioContext.currentTime
        // 根据当前状态决定目标音量
        const targetVolume = isRecording || isVoicePlaying ? LOW_VOLUME : FULL_VOLUME
        
        // 从0开始淡入
        gainNode.gain.cancelScheduledValues(currentTime)
        gainNode.gain.setValueAtTime(0, currentTime)
        gainNode.gain.linearRampToValueAtTime(targetVolume, currentTime + FADE_IN_DURATION / 1000)
        
        currentVolumeRef.current = targetVolume
        console.log(`🎵 [音量修复] BGM淡入: 0 -> ${targetVolume} (${FADE_IN_DURATION/1000}秒)`)
      }
      
      // 播放音频
      console.log('🎵 [音量修复] 开始播放BGM...')
      await audioElementRef.current.play()
      isPlayingRef.current = true
      pendingPlayRef.current = false
      console.log('🎵 [音量修复] BGM播放成功！')
    } catch (error) {
      console.error('❌ [音量修复] BGM播放失败:', error)
      // 标记为待播放，等待下次用户交互
      pendingPlayRef.current = true
    }
  }, [isRecording, isVoicePlaying, setVolume])
  
  // 用户交互处理函数
  const handleUserInteraction = useCallback(async () => {
    console.log('👆 [音量修复] 检测到用户交互')
    
    // 初始化音频
    initAudio()
    
    // 恢复AudioContext
    if (audioContextRef.current && audioContextRef.current.state === 'suspended') {
      try {
        await audioContextRef.current.resume()
        console.log('🎵 [音量修复] AudioContext已恢复')
      } catch (err) {
        console.warn('⚠️ [音量修复] AudioContext恢复失败:', err)
      }
    }
    
    // 如果有待播放的BGM，立即播放
    if (pendingPlayRef.current || (currentBGM && !isPlayingRef.current)) {
      console.log('🎵 [音量修复] 用户交互后播放BGM')
      await playBGM()
    }
  }, [initAudio, playBGM, currentBGM])
  
  // 当应用准备就绪时，初始化并预加载BGM
  useEffect(() => {
    if (!isAppReady) return
    
    const setupBGM = async () => {
      // 初始化音频系统
      initAudio()
      
      // 选择BGM
      if (!currentBGM) {
        const bgmPath = selectRandomBGM()
        if (bgmPath) {
          setCurrentBGM(bgmPath)
          console.log('🎵 [音量修复] BGM已选择:', bgmPath)
          
          // 预加载BGM
          try {
            await preloadBGM(bgmPath)
            pendingPlayRef.current = true // 标记为待播放
            
            // 尝试自动播放（桌面端可能成功）
            const isMobile = /Mobile|Android|iPhone|iPad/i.test(navigator.userAgent)
            if (!isMobile) {
              // 桌面端尝试自动播放
              setTimeout(() => {
                playBGM()
              }, 500)
            } else {
              console.log('🎵 [音量修复] 移动端检测到，等待用户交互后播放')
            }
          } catch (err) {
            console.error('❌ BGM预加载失败:', err)
          }
        }
      } else if (pendingPlayRef.current) {
        // BGM已选择但未播放，尝试播放
        playBGM()
      }
    }
    
    setupBGM()
  }, [isAppReady, currentBGM, initAudio, selectRandomBGM, preloadBGM, playBGM])
  
  // 监听用户交互事件（用于恢复AudioContext和播放BGM）
  useEffect(() => {
    if (!isAppReady) return
    
    // 监听多种交互事件
    const events = ['touchstart', 'touchend', 'click', 'keydown', 'mousedown']
    
    events.forEach(event => {
      document.addEventListener(event, handleUserInteraction, { 
        passive: true, 
        capture: true 
      })
    })
    
    return () => {
      events.forEach(event => {
        document.removeEventListener(event, handleUserInteraction, { capture: true })
      })
    }
  }, [isAppReady, handleUserInteraction])
  
  // 【音量修复】监听录音和语音播放状态，动态调整音量
  useEffect(() => {
    // 只有在BGM正在播放时才调整音量
    if (!isPlayingRef.current) {
      console.log('🎵 [音量修复] BGM未在播放，跳过音量调整')
      return
    }
    
    if (!gainNodeRef.current || !audioContextRef.current) {
      console.log('🎵 [音量修复] GainNode未初始化，跳过音量调整')
      return
    }
    
    const shouldLowerVolume = isRecording || isVoicePlaying
    const targetVolume = shouldLowerVolume ? LOW_VOLUME : FULL_VOLUME
    
    // 只有当目标音量与当前不同时才调整
    if (Math.abs(currentVolumeRef.current - targetVolume) < 0.01) {
      console.log('🎵 [音量修复] 目标音量相同，跳过调整')
      return
    }
    
    console.log(`🎵 [音量修复] 状态变化 - isRecording: ${isRecording}, isVoicePlaying: ${isVoicePlaying}`)
    console.log(`🎵 [音量修复] 音量调整: ${shouldLowerVolume ? '降低到30%' : '恢复到100%'} (${currentVolumeRef.current.toFixed(2)} -> ${targetVolume})`)
    
    setVolume(targetVolume, 0.5)
  }, [isRecording, isVoicePlaying, setVolume])
  
  // 清理函数
  useEffect(() => {
    return () => {
      if (audioElementRef.current) {
        audioElementRef.current.pause()
        audioElementRef.current.src = ''
        audioElementRef.current = null
      }
      if (audioContextRef.current && audioContextRef.current.state !== 'closed') {
        audioContextRef.current.close()
      }
      isPlayingRef.current = false
      isInitializedRef.current = false
    }
  }, [])
  
  // 停止BGM
  const stopBGM = useCallback(() => {
    if (audioElementRef.current) {
      audioElementRef.current.pause()
      audioElementRef.current.currentTime = 0
    }
    isPlayingRef.current = false
    console.log('🎵 BGM已停止')
  }, [])
  
  return { currentBGM, stopBGM, playBGM }
}





