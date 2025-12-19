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
      
      console.log('🎵 BGM开始播放:', bgmPath)
    } catch (error) {
      console.error('❌ BGM加载失败:', error)
    }
  }
  
  // 当应用准备就绪时，随机选择并播放BGM
  useEffect(() => {
    if (isAppReady && !currentBGM && !isPlayingRef.current) {
      const bgmPath = selectRandomBGM()
      if (bgmPath) {
        setCurrentBGM(bgmPath)
        
        // 【测试优化】移动端：延迟加载BGM，确保AudioContext已初始化
        // 移动端浏览器需要用户交互才能播放音频，所以延迟一点
        const delay = /Mobile|Android|iPhone|iPad/i.test(navigator.userAgent) ? 500 : 0
        setTimeout(() => {
          loadAndPlayBGM(bgmPath)
        }, delay)
      }
    }
  }, [isAppReady, currentBGM])
  
  // 【测试优化】移动端：监听用户交互，恢复AudioContext
  useEffect(() => {
    if (!isAppReady) return
    
    const handleUserInteraction = () => {
      if (audioContextRef.current && audioContextRef.current.state === 'suspended') {
        audioContextRef.current.resume().then(() => {
          console.log('🎵 [移动端优化] 用户交互后AudioContext已恢复')
          // 如果BGM还没播放，尝试播放
          if (!isPlayingRef.current && currentBGM) {
            loadAndPlayBGM(currentBGM)
          }
        }).catch(err => {
          console.warn('⚠️ [移动端优化] 恢复AudioContext失败:', err)
        })
      }
    }
    
    // 监听用户交互事件（移动端需要）
    document.addEventListener('touchstart', handleUserInteraction, { once: true })
    document.addEventListener('click', handleUserInteraction, { once: true })
    
    return () => {
      document.removeEventListener('touchstart', handleUserInteraction)
      document.removeEventListener('click', handleUserInteraction)
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

