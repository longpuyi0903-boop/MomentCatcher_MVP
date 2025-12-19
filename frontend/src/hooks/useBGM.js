import { useEffect, useRef, useState } from 'react'

/**
 * BGM管理器Hook
 * 功能：
 * 1. 随机选择并播放BGM
 * 2. 自动循环播放
 * 3. 音量淡入（3秒）
 * 4. 录音/语音播放时音量降到30%
 */
export const useBGM = (isAppReady, isRecording, isVoicePlaying) => {
  const audioContextRef = useRef(null)
  const gainNodeRef = useRef(null)
  const sourceRef = useRef(null)
  const audioBufferRef = useRef(null)
  const [currentBGM, setCurrentBGM] = useState(null)
  const isPlayingRef = useRef(false)
  const fadeInTimeoutRef = useRef(null)
  
  // BGM文件列表（需要手动维护，添加新BGM时更新此列表）
  const bgmFiles = [
    'Hans Zimmer - Interstellar - Main Theme (Piano Version)  Sheet Music.mp3'
    // 后续添加更多BGM时，在这里添加文件名
  ]
  
  // 音量常量
  const FULL_VOLUME = 0.6 // 正常音量（60%）
  const LOW_VOLUME = 0.18 // 降低后的音量（30% of 60%）
  const FADE_IN_DURATION = 3000 // 淡入时长（3秒）
  
  // 初始化AudioContext（延迟到需要时创建，避免浏览器限制）
  const initAudioContext = () => {
    if (!audioContextRef.current) {
      try {
        audioContextRef.current = new (window.AudioContext || window.webkitAudioContext)()
        gainNodeRef.current = audioContextRef.current.createGain()
        gainNodeRef.current.connect(audioContextRef.current.destination)
        gainNodeRef.current.gain.value = 0 // 初始音量为0
        console.log('🎵 AudioContext初始化成功')
        
        // 【测试优化】移动端：立即尝试恢复AudioContext（需要用户交互）
        if (audioContextRef.current.state === 'suspended') {
          // 尝试恢复（可能需要用户交互）
          audioContextRef.current.resume().then(() => {
            console.log('🎵 [移动端优化] AudioContext已恢复')
          }).catch(err => {
            console.warn('⚠️ [移动端优化] AudioContext恢复失败，需要用户交互:', err)
          })
        }
      } catch (error) {
        console.error('❌ AudioContext初始化失败:', error)
      }
    } else if (audioContextRef.current.state === 'suspended') {
      // 如果AudioContext被暂停，尝试恢复
      audioContextRef.current.resume().then(() => {
        console.log('🎵 AudioContext已恢复')
      }).catch(err => {
        console.warn('⚠️ AudioContext恢复失败，可能需要用户交互:', err)
      })
    }
  }
  
  useEffect(() => {
    return () => {
      // 清理资源
      if (fadeInTimeoutRef.current) {
        clearTimeout(fadeInTimeoutRef.current)
      }
      if (sourceRef.current) {
        try {
          sourceRef.current.stop()
        } catch (e) {
          // 忽略错误
        }
        sourceRef.current = null
      }
      if (audioContextRef.current && audioContextRef.current.state !== 'closed') {
        audioContextRef.current.close()
      }
    }
  }, [])
  
  // 随机选择BGM
  const selectRandomBGM = () => {
    if (bgmFiles.length === 0) return null
    const randomIndex = Math.floor(Math.random() * bgmFiles.length)
    // 使用相对路径，Vite会自动处理public目录
    return `/bgm/${bgmFiles[randomIndex]}`
  }
  
  // 加载并播放BGM
  const loadAndPlayBGM = async (bgmPath) => {
    try {
      // 确保AudioContext已初始化
      initAudioContext()
      const audioContext = audioContextRef.current
      if (!audioContext) {
        console.error('❌ AudioContext未初始化')
        return
      }
      
      // 如果已经有音频在播放，先停止
      if (sourceRef.current) {
        try {
          sourceRef.current.stop()
        } catch (e) {
          // 忽略错误
        }
        sourceRef.current = null
      }
      
      // 加载音频文件（URL编码处理空格和特殊字符）
      const encodedPath = encodeURI(bgmPath)
      console.log('🎵 加载BGM:', encodedPath)
      const response = await fetch(encodedPath)
      if (!response.ok) {
        throw new Error(`BGM加载失败: ${response.status} ${response.statusText}`)
      }
      const arrayBuffer = await response.arrayBuffer()
      const audioBuffer = await audioContext.decodeAudioData(arrayBuffer)
      audioBufferRef.current = audioBuffer
      
      // 创建音频源
      const source = audioContext.createBufferSource()
      source.buffer = audioBuffer
      source.loop = true // 循环播放
      source.connect(gainNodeRef.current)
      
      sourceRef.current = source
      
      // 【移动端修复】确保AudioContext在运行状态
      if (audioContext.state === 'suspended') {
        await audioContext.resume()
        console.log('🎵 [移动端修复] 播放前恢复AudioContext')
      }
      
      // 开始播放
      source.start(0)
      isPlayingRef.current = true
      
      // 音量淡入
      const gainNode = gainNodeRef.current
      const currentTime = audioContext.currentTime
      const targetVolume = isRecording || isVoicePlaying ? LOW_VOLUME : FULL_VOLUME
      
      gainNode.gain.cancelScheduledValues(currentTime)
      gainNode.gain.setValueAtTime(0, currentTime)
      gainNode.gain.linearRampToValueAtTime(targetVolume, currentTime + FADE_IN_DURATION / 1000)
      
      console.log('🎵 BGM开始播放:', bgmPath, 'AudioContext状态:', audioContext.state, '音量:', targetVolume)
    } catch (error) {
      console.error('❌ BGM加载失败:', error)
    }
  }
  
  // 当应用准备就绪时，随机选择BGM（但不立即播放，等待用户交互）
  useEffect(() => {
    if (isAppReady && !currentBGM && !isPlayingRef.current) {
      const bgmPath = selectRandomBGM()
      if (bgmPath) {
        setCurrentBGM(bgmPath)
        console.log('🎵 [移动端修复] BGM已选择，等待用户交互:', bgmPath)
        
        // 【移动端修复】移动端不自动播放，等待用户交互
        // 桌面端可以尝试自动播放
        const isMobile = /Mobile|Android|iPhone|iPad/i.test(navigator.userAgent)
        if (!isMobile) {
          // 桌面端：延迟一点后尝试播放
          setTimeout(() => {
            loadAndPlayBGM(bgmPath)
          }, 500)
        }
        // 移动端：等待用户交互（在handleUserInteraction中播放）
      }
    }
  }, [isAppReady, currentBGM])
  
  // 【移动端修复】监听任何用户交互（不限于麦克风），恢复AudioContext并播放BGM
  useEffect(() => {
    if (!isAppReady) return
    
    const handleUserInteraction = async () => {
      console.log('👆 [移动端修复] 检测到用户交互，恢复AudioContext并播放BGM')
      
      // 初始化AudioContext（如果还没初始化）
      initAudioContext()
      
      // 恢复AudioContext（如果被暂停）
      if (audioContextRef.current) {
        if (audioContextRef.current.state === 'suspended') {
          try {
            await audioContextRef.current.resume()
            console.log('🎵 [移动端修复] AudioContext已恢复，状态:', audioContextRef.current.state)
          } catch (err) {
            console.warn('⚠️ [移动端修复] 恢复AudioContext失败:', err)
            return
          }
        }
        
        // 确保AudioContext在运行状态
        if (audioContextRef.current.state === 'running') {
          console.log('🎵 [移动端修复] AudioContext运行中，尝试播放BGM')
          // 如果BGM还没播放，立即播放
          if (!isPlayingRef.current) {
            if (currentBGM) {
              console.log('🎵 [移动端修复] 使用已有BGM:', currentBGM)
              await loadAndPlayBGM(currentBGM)
            } else {
              // 如果BGM还没选择，选择并播放
              const bgmPath = selectRandomBGM()
              if (bgmPath) {
                console.log('🎵 [移动端修复] 选择新BGM:', bgmPath)
                setCurrentBGM(bgmPath)
                await loadAndPlayBGM(bgmPath)
              }
            }
          } else {
            console.log('🎵 [移动端修复] BGM已在播放')
          }
        } else {
          console.warn('⚠️ [移动端修复] AudioContext状态异常:', audioContextRef.current.state)
        }
      } else {
        console.warn('⚠️ [移动端修复] AudioContext未初始化')
      }
    }
    
    // 【移动端修复】监听所有用户交互事件（不限制次数，确保BGM能播放）
    // 使用capture阶段，确保能捕获到所有交互（包括按钮点击）
    document.addEventListener('touchstart', handleUserInteraction, { passive: true, capture: true })
    document.addEventListener('click', handleUserInteraction, { passive: true, capture: true })
    
    return () => {
      document.removeEventListener('touchstart', handleUserInteraction, { capture: true })
      document.removeEventListener('click', handleUserInteraction, { capture: true })
    }
  }, [isAppReady, currentBGM])
  
  // 监听录音和语音播放状态，动态调整音量
  useEffect(() => {
    if (!gainNodeRef.current || !isPlayingRef.current) return
    
    // 确保AudioContext已初始化
    initAudioContext()
    const gainNode = gainNodeRef.current
    const audioContext = audioContextRef.current
    if (!audioContext) return
    
    const shouldLowerVolume = isRecording || isVoicePlaying
    const targetVolume = shouldLowerVolume ? LOW_VOLUME : FULL_VOLUME
    const currentTime = audioContext.currentTime
    
    // 平滑过渡到目标音量（0.5秒过渡）
    gainNode.gain.cancelScheduledValues(currentTime)
    gainNode.gain.setValueAtTime(gainNode.gain.value, currentTime)
    gainNode.gain.linearRampToValueAtTime(targetVolume, currentTime + 0.5)
    
    console.log(`🎵 BGM音量调整: ${shouldLowerVolume ? '降低到30%' : '恢复到100%'}`)
  }, [isRecording, isVoicePlaying])
  
  // 清理函数
  const stopBGM = () => {
    if (sourceRef.current) {
      try {
        sourceRef.current.stop()
      } catch (e) {
        // 忽略错误
      }
      sourceRef.current = null
    }
    isPlayingRef.current = false
  }
  
  return { currentBGM, stopBGM }
}

