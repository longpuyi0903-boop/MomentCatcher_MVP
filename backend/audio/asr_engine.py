"""
ASR Engine - 语音识别（Speech to Text）
使用阿里云 DashScope 语音识别 API
"""

import os
import json
import requests
from pathlib import Path
from dotenv import load_dotenv
from http import HTTPStatus
import dashscope
from dashscope import Files
from dashscope.audio.asr import Transcription

# 加载环境变量
# 先尝试从系统环境变量读取（Railway等云平台）
DASHSCOPE_API_KEY = os.getenv("ALIYUN_QWEN_KEY")
# 如果系统环境变量没有，再尝试从.env文件加载
if not DASHSCOPE_API_KEY:
    load_dotenv()
    DASHSCOPE_API_KEY = os.getenv("ALIYUN_QWEN_KEY")
if not DASHSCOPE_API_KEY:
    raise EnvironmentError("ALIYUN_QWEN_KEY not found. Please check your environment variables or .env file.")

# 设置 DashScope API Key
dashscope.api_key = DASHSCOPE_API_KEY


def speech_to_text(audio_file_path: str) -> str:
    """
    将语音转换为文字
    
    Args:
        audio_file_path: 音频文件路径（支持 wav, mp3, m4a 等格式）
    
    Returns:
        str: 识别出的文字内容
    """
    
    audio_path = Path(audio_file_path)
    
    if not audio_path.exists():
        print(f"❌ 音频文件不存在: {audio_file_path}")
        return None
    
    try:
        print(f"🎤 正在识别语音...")
        
        # 步骤1：上传文件到 DashScope Files API，获取 file_id
        file_response = Files.upload(file_path=str(audio_path), purpose='file-extract')
        
        if not file_response or file_response.status_code != 200:
            print(f"❌ 文件上传失败")
            if hasattr(file_response, 'message'):
                print(f"   错误: {file_response.message}")
            return None
        
        # 从 output.uploaded_files[0].file_id 获取 file_id
        try:
            if hasattr(file_response, 'output') and hasattr(file_response.output, 'uploaded_files'):
                uploaded_files_list = file_response.output.uploaded_files
            elif hasattr(file_response, 'output') and isinstance(file_response.output, dict) and 'uploaded_files' in file_response.output:
                uploaded_files_list = file_response.output['uploaded_files']
            else:
                raise AttributeError("响应中没有 'uploaded_files' 字段")
            
            if not uploaded_files_list or len(uploaded_files_list) == 0:
                raise ValueError("上传成功但响应中 'uploaded_files' 列表为空")
            
            uploaded_file_info = uploaded_files_list[0]
            
            if hasattr(uploaded_file_info, 'file_id'):
                file_id = uploaded_file_info.file_id
            elif isinstance(uploaded_file_info, dict) and 'file_id' in uploaded_file_info:
                file_id = uploaded_file_info['file_id']
            else:
                raise AttributeError("Uploaded file info is missing 'file_id'")
                
        except (AttributeError, KeyError, ValueError, IndexError) as e:
            print(f"❌ 无法从响应中解析 file_id: {e}")
            return None
        
        # 步骤2：使用 Files.get() 获取带签名的文件 URL
        file_info = Files.get(file_id)
        
        if not file_info or file_info.status_code != 200:
            print(f"❌ 无法获取文件信息")
            if hasattr(file_info, 'message'):
                print(f"   错误: {file_info.message}")
            return None
        
        # 获取文件 URL（带签名）
        try:
            if hasattr(file_info, 'output') and hasattr(file_info.output, 'url'):
                file_url = file_info.output.url
            elif hasattr(file_info, 'output') and isinstance(file_info.output, dict) and 'url' in file_info.output:
                file_url = file_info.output['url']
            else:
                # 如果没有 url 字段，尝试使用 content_url
                if hasattr(file_info, 'output') and hasattr(file_info.output, 'content_url'):
                    file_url = file_info.output.content_url
                elif hasattr(file_info, 'output') and isinstance(file_info.output, dict) and 'content_url' in file_info.output:
                    file_url = file_info.output['content_url']
                else:
                    # 最后尝试：使用标准格式（但可能没有签名）
                    file_url = f"https://dashscope.aliyuncs.com/api/v1/files/{file_id}/content"
        except Exception as e:
            print(f"⚠️ 获取文件 URL 失败: {e}，使用标准格式")
            file_url = f"https://dashscope.aliyuncs.com/api/v1/files/{file_id}/content"
        
        # 步骤3：使用 SDK 的 Transcription.async_call + wait 方法
        
        # 提交异步任务
        task_response = Transcription.async_call(
            model='paraformer-v2',
            file_urls=[file_url],
            language_hints=['zh']
        )
        
        if task_response.status_code != HTTPStatus.OK:
            print(f"❌ ASR 任务提交失败: {task_response.status_code}")
            if hasattr(task_response, 'message'):
                print(f"   错误: {task_response.message}")
            return None
        
        task_id = task_response.output.task_id
        
        # 等待任务完成（SDK 会自动轮询）
        transcribe_response = Transcription.wait(task=task_id)
        
        if transcribe_response.status_code != HTTPStatus.OK:
            print(f"❌ ASR 任务执行失败: {transcribe_response.status_code}")
            if hasattr(transcribe_response, 'message'):
                print(f"   错误: {transcribe_response.message}")
            return None
        
        # 步骤4：提取识别结果
        output = transcribe_response.output
        
        text = None
        
        try:
            # 方式1 (优先): 从 results 字段中检查并下载 transcription_url
            # 直接使用 try-except 访问，避免 hasattr 触发 KeyError
            transcription_url = None
            first_result = None
            
            try:
                # 直接访问 results，如果不存在会抛出 KeyError
                results = output.results
                if results and len(results) > 0:
                    first_result = results[0]
                    
                    # 直接访问 transcription_url
                    try:
                        transcription_url = first_result.transcription_url
                    except (KeyError, AttributeError):
                        # 如果属性访问失败，尝试字典方式
                        try:
                            if isinstance(first_result, dict) and 'transcription_url' in first_result:
                                transcription_url = first_result['transcription_url']
                        except:
                            pass
            except (KeyError, AttributeError):
                # 尝试字典方式访问
                try:
                    if isinstance(output, dict) and 'results' in output:
                        results = output['results']
                        if results and len(results) > 0:
                            first_result = results[0]
                            if isinstance(first_result, dict) and 'transcription_url' in first_result:
                                transcription_url = first_result['transcription_url']
                except:
                    pass
            
            # 如果找到了 transcription_url，下载并解析结果
            if transcription_url:
                # 发起 HTTP GET 请求下载转录结果
                result_response = requests.get(transcription_url, timeout=30)
                
                if result_response.status_code == 200:
                    result_data = result_response.json()
                    
                    # ASR 结果文件通常是 JSON 数组（每个元素是一个句子）
                    if isinstance(result_data, list) and result_data:
                        # 提取所有句子的 text 字段
                        text_parts = []
                        for item in result_data:
                            if isinstance(item, dict):
                                # 尝试多种可能的字段名
                                if 'text' in item:
                                    text_parts.append(item['text'])
                                elif 'sentence' in item:
                                    text_parts.append(item['sentence'])
                                elif 'transcription' in item:
                                    text_parts.append(item['transcription'])
                        
                        if text_parts:
                            text = ' '.join(text_parts).strip()
                    # 兼容性：如果结果文件是单个 JSON 对象
                    elif isinstance(result_data, dict):
                        # 方式1：从 transcripts 数组提取（DashScope paraformer-v2 的标准格式）
                        if 'transcripts' in result_data and isinstance(result_data['transcripts'], list):
                            transcripts = result_data['transcripts']
                            if len(transcripts) > 0:
                                first_transcript = transcripts[0]
                                # 优先使用 transcripts[0].text（完整文本）
                                if isinstance(first_transcript, dict) and 'text' in first_transcript:
                                    text = first_transcript['text']
                                # 备用：从 sentences 中提取
                                elif isinstance(first_transcript, dict) and 'sentences' in first_transcript:
                                    sentences = first_transcript['sentences']
                                    if isinstance(sentences, list):
                                        text_parts = [s.get('text', '') for s in sentences if isinstance(s, dict) and 'text' in s]
                                        if text_parts:
                                            text = ' '.join(text_parts).strip()
                        
                        # 方式2：尝试其他可能的字段名（兼容性）
                        if not text:
                            if 'text' in result_data:
                                text = result_data['text']
                            elif 'transcription' in result_data:
                                text = result_data['transcription']
                            elif 'sentence_list' in result_data:
                                # 如果包含 sentence_list
                                sentence_list = result_data['sentence_list']
                                if isinstance(sentence_list, list):
                                    text_parts = [s.get('text', '') for s in sentence_list if isinstance(s, dict)]
                                    if text_parts:
                                        text = ' '.join(text_parts).strip()
                            elif 'sentences' in result_data:
                                # 如果包含 sentences（顶层）
                                sentences = result_data['sentences']
                                if isinstance(sentences, list):
                                    text_parts = []
                                    for s in sentences:
                                        if isinstance(s, dict) and 'text' in s:
                                            text_parts.append(s['text'])
                                        elif isinstance(s, str):
                                            text_parts.append(s)
                                    if text_parts:
                                        text = ' '.join(text_parts).strip()
            else:
                print(f"❌ 下载转录结果失败: {result_response.status_code}")
            
            # 兼容性（备用）：如果 API 未来版本直接在 results[0] 中嵌入了 text 字段
            if not text and first_result:
                try:
                    if hasattr(first_result, 'text') and first_result.text:
                        text = first_result.text
                except (KeyError, AttributeError):
                    pass
            
            # 兼容性（次要）：直接从 output.text 提取
            if not text:
                try:
                    if hasattr(output, 'text') and output.text:
                        text = output.text
                except (KeyError, AttributeError):
                    pass
                    
        except requests.exceptions.RequestException as e:
            print(f"❌ 网络请求失败: {e}")
            return None
        except json.JSONDecodeError as e:
            print(f"❌ JSON 解析失败: {e}")
            return None
        except requests.exceptions.RequestException as e:
            print(f"❌ 网络请求失败: {e}")
            return None
        except json.JSONDecodeError as e:
            print(f"❌ JSON 解析失败: {e}")
            return None
        except Exception as e:
            print(f"❌ 提取转录结果时发生错误: {e}")
            return None
        
        if text and text.strip():
            print(f"✅ 语音识别成功: {text}")
            return text.strip()
        else:
            print(f"⚠️ 识别结果为空（可能是静音或无法识别）")
            return None
        
    except requests.exceptions.RequestException as e:
        print(f"❌ 网络请求失败: {e}")
        return None
    except json.JSONDecodeError as e:
        print(f"❌ JSON 解析失败: {e}")
        return None
    except Exception as e:
        print(f"❌ 语音识别失败: {e}")
        return None


def test_asr():
    """测试 ASR 功能"""
    print("\n" + "="*60)
    print("🎤 ASR Engine 测试")
    print("="*60)
    print("💡 提示: 需要先有一个测试音频文件")
    print("   你可以用手机录一段音，保存为 test_audio.wav")
    print("="*60 + "\n")
    
    # 检查是否有测试文件
    test_file = "audio_outputs/test_audio.wav"
    if not Path(test_file).exists():
        print(f"❌ 测试文件不存在: {test_file}")
        print("💡 请先创建测试音频文件，然后再运行测试")
        return
    
    text = speech_to_text(test_file)
    
    if text:
        print("\n" + "="*60)
        print("✅ 测试成功！")
        print(f"📝 识别结果: {text}")
        print("="*60 + "\n")
    else:
        print("\n❌ 测试失败")


if __name__ == "__main__":
    test_asr()