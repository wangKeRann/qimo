from selenium import webdriver
from selenium.webdriver.edge.service import Service
from selenium.webdriver.edge.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import time
import msvcrt

def setup_driver():
    """设置浏览器驱动"""
    try:
        # 读取配置
        username, password, driver_path = read_config()
        if not driver_path:
            # 如果没有配置文件或配置不完整，要求手动输入
            driver_path = input("请输入浏览器驱动程序位置：（例如C:\\Users\\kang\\Downloads\\msedgedriver.exe）")
        
        edge_options = Options()
        # 添加这些选项来禁用日志和声音
        edge_options.add_argument('--disable-gpu')
        edge_options.add_argument('--no-sandbox')
        edge_options.add_argument('--disable-dev-shm-usage')
        edge_options.add_argument('--log-level=3')  # 只显示致命错误
        edge_options.add_argument('--silent')  # 静默模式
        edge_options.add_argument('--mute-audio')  # 禁用声音
        edge_options.add_experimental_option('excludeSwitches', ['enable-logging'])  # 禁用日志
        
        # 添加其他禁用声音的选项
        edge_options.add_experimental_option('prefs', {
            'profile.default_content_setting_values.media_stream_mic': 2,  # 禁用麦克风
            'profile.default_content_setting_values.media_stream_camera': 2,  # 禁用摄像头
            'profile.default_content_setting_values.notifications': 2,  # 禁用通知
            'profile.managed_default_content_settings.sound': 2  # 禁用声音
        })
        
        service = Service(
            driver_path,
            service_args=['--silent'],  # 静默参数
            log_output='NUL'  # Windows下将日志重定向到空设备
        )
        
        driver = webdriver.Edge(service=service, options=edge_options)
        print("----------------------------------------------")
        return driver
        
    except Exception as e:
        print(f"设置浏览器驱动时出错: {str(e)}")
        print("请检查驱动程序路径是否正确")
        return None

def pause_video(driver):
    """模拟点击播放/暂停按钮"""
    try:
        result = driver.execute_script("""
            function simulateClick(element) {
                // 创建鼠标移动事件
                element.dispatchEvent(new MouseEvent('mouseover', {
                    bubbles: true,
                    cancelable: true,
                    view: window
                }));
                
                // 短暂延迟后点击
                return new Promise(resolve => {
                    setTimeout(() => {
                        // 创建点击事件
                        element.dispatchEvent(new MouseEvent('click', {
                            bubbles: true,
                            cancelable: true,
                            view: window
                        }));
                        resolve(true);
                    }, 100);
                });
            }
            
            var video = document.querySelector('video');
            if (!video) return { success: false, message: '未找到视频' };
            
            // 查找播放按钮
            var playButton = document.querySelector('.prism-play-btn');
            if (!playButton) {
                console.log('未找到播放按钮，尝试点击视频区域');
                // 如果找不到播放按钮，尝试点击视频本身
                return simulateClick(video).then(() => ({
                    success: true,
                    paused: video.paused
                }));
            }
            
            // 点击播放按钮
            return simulateClick(playButton).then(() => ({
                success: true,
                paused: video.paused
            }));
        """)
        
        if result.get('success'):
            status = "暂停" if result.get('paused') else "播放"
            print(f"视频已{status}")
        else:
            print(result.get('message', '操作失败'))
            
    except Exception as e:
        print(f"控制视频播放时出错: {str(e)}")

def mute_video(driver):
    driver.execute_script("""
        var video = document.querySelector('video');
        video.muted = !video.muted;
        console.log(video.muted ? '已静音' : '已取消静音');
    """)

def get_sattus(driver):
    status = driver.execute_script("""
        var video = document.querySelector('video');
        return {
            current: video.currentTime,
            duration: video.duration,
            buffered: video.buffered.length ? 
                video.buffered.end(video.buffered.length-1) : 0,
            readyState: video.readyState,
            networkState: video.networkState
        };
    """)
    print(f"当前时间: {int(status['current'])}秒")
    print(f"总时长: {int(status['duration'])}秒")
    print(f"已缓冲: {int(status['buffered'])}秒")
    print(f"就绪状态: {status['readyState']}/4")
    print(f"网络状态: {status['networkState']}")

def set_speed(driver, speed):
    driver.execute_script(f"""
        var video = document.querySelector('video');
        video.playbackRate = {speed};
        console.log('播放速度已设置为 {speed}x');
    """)

def get_video(driver):
    """检测视频元素"""
    try:
        # 使用JavaScript检视频元素
        video_status = driver.execute_script("""
            function checkVideo() {
                var video = document.querySelector('video');
                if (!video) {
                    // 如果没找到video标签，检查是否在iframe中
                    var iframes = document.getElementsByTagName('iframe');
                    for (var i = 0; i < iframes.length; i++) {
                        try {
                            video = iframes[i].contentDocument.querySelector('video');
                            if (video) break;
                        } catch (e) {
                            console.log('无法访问iframe:', e);
                        }
                    }
                }
                
                if (!video) return { exists: false };
                
                return {
                    exists: true,
                    readyState: video.readyState,
                    src: video.src,
                    duration: video.duration,
                    paused: video.paused
                };
            }
            return checkVideo();
        """)
        
        if not video_status['exists']:
            print("未找到视频元素")
            return False
            
        print(f"\n视频状态:")
        print(f"绪状态: {video_status['readyState']}/4")
        print(f"时长: {video_status['duration']}秒")
        print(f"是否暂停: {'是' if video_status['paused'] else '否'}")
        
        return True
        
    except Exception as e:
        print(f"检查视频时出错: {str(e)}")
        return False

def simulate_human_input(driver, username, password):
    """模拟人类输入行为"""
    try:
        driver.execute_script("""
            function simulateTyping(element, text) {
                element.focus();
                element.click();
                element.value = '';  // 清空输入框
                
                return new Promise((resolve) => {
                    let i = 0;
                    function typeChar() {
                        if (i < text.length) {
                            // 模拟输入单个字符
                            element.value += text[i];
                            
                            // 触发输入事件
                            element.dispatchEvent(new Event('input', { bubbles: true }));
                            element.dispatchEvent(new Event('change', { bubbles: true }));
                            
                            // 随机延迟50-150ms
                            i++;
                            setTimeout(typeChar, Math.random() * 100 + 50);
                        } else {
                            resolve();
                        }
                    }
                    typeChar();
                });
            }
            
            async function fillForm(username, password) {
                const usernameInput = document.querySelector('#login_name');
                const passwordInput = document.querySelector('#password');
                
                if (!usernameInput || !passwordInput) {
                    throw new Error('未找到输入框');
                }
                
                // 先输入用户名
                await simulateTyping(usernameInput, username);
                // 等待一下再输入密码
                await new Promise(resolve => setTimeout(resolve, 500));
                // 输入密码
                await simulateTyping(passwordInput, password);
                
                return true;
            }
            
            return fillForm(arguments[0], arguments[1]);
        """, username, password)
        
        print("正在输入登录信息...")
        time.sleep(2)  # 等待输入完成
        
    except Exception as e:
        print(f"模拟输入时出错: {str(e)}")
        return False

def init():
    print("正在初始化，请勿操作...")
    driver = setup_driver()
    if not driver:
        print("浏览器驱动初始化失败")
        return None
    
    # 读取配置（重用之前读取的配置）
    username, password, _ = read_config()
    if not username or not password:
        print("请手动登录...")
    else:
        # 访问主页
        driver.get("https://www.zjooc.cn")
        time.sleep(2)
        
        try:
            # 点击"请登录"链接
            driver.execute_script("""
                var loginLink = document.querySelector('a[href="javascript:void(0);"]');
                if (loginLink && loginLink.textContent.trim() === '请登录') {
                    loginLink.click();
                } else {
                    throw new Error('未找到登录链接');
                }
            """)
            
            # 等待登录框出现
            time.sleep(2)
            
            # 模拟人类输入行为
            simulate_human_input(driver, username, password)
            
            print("登录信息已输入，请输入验证码后点击登录...")
            
        except Exception as e:
            print(f"自动登录失败: {str(e)}")
            print("请手动登录...")

    print("\n浏览器已启动，请登录并进入视频播放页面")
    print("！！！！！请入视频播放页面后继续操作！！！！！")
    print("------------------------------------")
    return driver

def check_pause_status(driver):
    """检查是否需要暂停"""
    try:
        # 检查是否按下了暂停键
        if msvcrt.kbhit():  # Windows系统
            if msvcrt.getch() == b'p':
                print("\n检测到手动暂停")
                return True
           
        return False
        
    except Exception as e:
        print(f"\n检查暂停状态时出错: {str(e)}")
        return False

def wait_for_resume(driver):
    """等待恢复播放"""
    print("\n播放已暂停，请选择操作：")
    print("1. 继续播放")
    print("2. 检查视频状态")
    print("3. 设置播放速度")
    print("4. 设置静音")
    print("5. 手动点击完成按钮")
    print("6. 手动模式")
    choice = input("请输入选项(直接回车继续播放): ")
    
    try:
        if choice == '2':
            get_video(driver)
            return wait_for_resume(driver)  # 继续等待
        elif choice == '3':
            new_speed = input("请输入新的播放速度(0.5-4): ")
            set_speed(driver, new_speed)
            return wait_for_resume(driver)  # 继续等待
        elif choice == '4':
            mute_video(driver)
            return wait_for_resume(driver)  # 继续等待
        elif choice == '5':
            click_complete_button(driver)
            return wait_for_resume(driver)  # 继续等待
        elif choice == '6':
            manual_play(driver)
            return wait_for_resume(driver)  # 继续等待

        
        pause_video(driver)
        print("继续播放...")
        
    except Exception as e:
        print(f"恢复播放时出错: {str(e)}")

def check_video_progress(driver):
    """检查视频播放进度"""
    try:
        # 首先检查是否需要暂停
        if check_pause_status(driver):
            wait_for_resume(driver)
            return False
            
        status = driver.execute_script("""
            var video = document.querySelector('video');
            if (!video) return null;
            
            
            
            return {
                currentTime: video.currentTime,
                duration: video.duration,
                ended: video.ended,
                paused: video.paused,
                readyState: video.readyState,
                lastTime: video.lastCheckTime || 0
            };
        """)
        
        if not status:
            return False
            
        # 检查是否播放完成（允许1秒误差）
        is_complete = (status['ended'] or 
                      (status['currentTime'] >= status['duration'] - 1 if status['duration'] else False))
                      
        if is_complete:
            print("\n视频已播放完成！")
        else:
            # 检查是否卡住（当前时间与上次检查时间相同）
            current_time = status['currentTime']
            last_time = status.get('lastTime', 0)
            
            if current_time == last_time:
                trycount = 0
                # 先尝试恢复播放
                while trycount < 2:
                    print("\n检测到视频可能卡住，可能是网络问题，正在尝试恢复播放...请勿着急，最小化也会导致显示一次这条消息，彻底失败后再操作")
                    time.sleep(5)
                    pause_video(driver)
                    
                    time.sleep(5)

                    # 检查是否已经恢复播放
                    new_status = driver.execute_script("""
                        var video = document.querySelector('video');
                        if (!video) return null;
                        video.play();
                        return {
                            currentTime: video.currentTime,
                            playing: !video.paused
                        };
                    """)
                    
                    if new_status and new_status['currentTime'] > current_time:
                        print("视频已恢复播放")
                        break
                        
                    trycount += 1
                    
                # 如果恢复播放失败，则尝试刷新页面
                if trycount == 2:
                    print("\n尝试恢复播放失败，准备刷新页面...")
                    driver.refresh()
                    time.sleep(5)
                    jump_to_next_unwatched_video(driver)
                    time.sleep(5)
                    set_speed(driver, 4)
                    mute_video(driver)
                    pause_video(driver)
                    
                    # 给页面一些时间加载
                    time.sleep(2)
                    # 检查视频是否正常
                    if not get_video(driver):
                        print("\n视频加载失败，请手动操作...")
                        return False
                    
            # 更新上次检查时间
            driver.execute_script("""
                var video = document.querySelector('video');
                if (video) video.lastCheckTime = arguments[0];
            """, current_time)
            
            # 显示进度条
            progress = (current_time / status['duration']) * 100
            bar_length = 50
            filled_length = int(bar_length * progress // 100)
            bar = '=' * filled_length + '-' * (bar_length - filled_length)
            
            print(f'\r进度: [{bar}] {progress:.1f}% ({int(current_time)}/{int(status["duration"])}秒)', end='')
            
        return is_complete
        
    except Exception as e:
        print(f"\n检查视频进度时出错: {str(e)}")
        time.sleep(3)
        return False

def wait_for_user_action():
    """等待用户操作"""
    print("\n程序已暂停，请选择操作：")
    print("1. 继续执行")
    print("2. 检查视频状态")
    print("3. 设置播放速度")
    print("4. 设置静音")
    print("5. 手动点击完成按钮")
    print("6. 手动模式")
    choice = input("请输入选项(直接回车继续执行): ")
    
    return choice

def auto_play(driver):
    """自动播放模式"""
    try:
        print("自动模式")
        print("请输入视频播放速度(0.5-4): ")
        speed = input()
        print("是否静音(y/n): ")
        mute = input()
        print("------------------------------------\n")
        
        print("读取章节")
        chapters = get_chapters(driver)
        print("章节读取完毕")
        print("------------------------------------\n")
        
        # 添加暂停标志
        paused = False

        for chapter_index, chapter in enumerate(chapters, 1):
            print(f"\n进入章节: {chapter['title']}")
            for section_index, section in enumerate(chapter['sections'], 1):
                print(f"\n进入小节: {section['title']}")
                
                # 检查是否按下了暂停键
                if msvcrt.kbhit():  # Windows系统
                    if msvcrt.getch() == b'p':
                        paused = True
                
                if paused:
                    choice = wait_for_user_action()
                    if choice == '2':
                        get_video(driver)
                        paused = True  # 继续等待
                    elif choice == '3':
                        new_speed = input("请输入新的播放速度(0.5-4): ")
                        set_speed(driver, new_speed)
                        paused = True  # 继续等待
                    elif choice == '4':
                        mute_video(driver)
                        paused = True  # 继续等待
                    elif choice == '5':
                        click_complete_button(driver)
                        paused = True  # 继续等待
                    else:
                        paused = False  # 继续执行
                        print("\n继续执行程序...")
                
                click_chapter(driver, chapter_index, section_index)
                time.sleep(2)  # 等待页面加载
                
                print("检查任务列表")
                if get_video_list(driver):
                    while True:  # 循环处理所有未完成的视频
                        print("\n跳转到未完成任务...")
                        if jump_to_next_unwatched_video(driver):
                            time.sleep(2)  # 等待视频加载
                            
                            if get_video(driver):
                                set_speed(driver, speed)
                                if mute == 'y':
                                    print("开启静音")
                                    mute_video(driver)
                                time.sleep(5)
                                pause_video(driver)  # 开始播放
                                time.sleep(5)
                                # 获取视频长度并跳转到倒数第3秒
                                video_info = driver.execute_script("""
                                    var video = document.querySelector('video');
                                    if (!video) return null;
                                    return {
                                        duration: video.duration
                                    };
                                """)
                                
                                if video_info and video_info['duration']:
                                    target_time = video_info['duration'] - 3
                                    print(f"\n视频总长: {int(video_info['duration'])}秒")
                                    print(f"跳转到: {int(target_time)}秒")
                                    seek_video(driver, target_time)
                                    time.sleep(5)  # 等待跳转完成
                                
                                pause_video(driver)  # 开始播放
                                
                                
                                print("等待视频播放完成...")
                                while not check_video_progress(driver):
                                    time.sleep(1)  # 每秒检查一次进度
                                
                                # 视频播放完成后刷新页面
                                print("\n休息5秒后刷新页面...")
                                time.sleep(5)
                                
                                driver.refresh()
                                time.sleep(5)  # 等待页面加载
                                
                            else:
                                print("检测按钮状态")

                                if check_complete_button(driver):
                                    click_complete_button(driver)
                                    # 点击按钮后刷新页面
                                    print("\n刷新页面...")
                                    
                                    driver.refresh()
                                    time.sleep(3)
                            
                                else:
                                    print("未检测到按钮或视频")
                                    
                        else:
                            print("当前小节的任务都已完成")
                            break
                            
                else:
                    print("------------------------------------\n")
                    
        print("\n所有章节已完成！回车退出")
        input()
        
    except Exception as e:
        print(f"\n自动播放出错: {str(e)}")
        print("是否重试？(y/n)")
        if input().lower() == 'y':
            auto_play(driver)

def manual_play(driver):
    try:
        print("\n请选择模式")
        print("1. 跳转章节")
        print("2. 检查按钮")
        print("3. 检查视频")
        print("4. 获取任务列表")
        print("5. 获取下一个未完成任务")
        print("6. 跳转到下一个未完成任务")
        print("7. 设置播放速度")
        print("8. 设置视频清晰度")
        print("9. 设置静音")
        print("10. 刷新网页")
        print("11. 跳转到指定时间")  # 新增选项
        print("p. 暂停/继续播放")
        print("q. 退出")
        mode = input("请输入选项: ")
        
        if mode.lower() == 'p':
            pause_video(driver)
            manual_play(driver)
            return
            
        if mode == '1':
            chapter_index = input("请输入章节索引: ")
            section_index = input("请输入小节索引: ")
            click_chapter(driver, chapter_index, section_index)
        elif mode == '2':
            status = check_complete_button(driver)
            if status == 0:
                print("未检测到按钮")
            elif status == 1:
                print("按钮已被点击")
            elif status == 2:
                print("按钮未点击") 
                input()
                click_complete_button(driver)
        elif mode == '3':
            if get_video(driver):
                print("检测到视频存在")
            else:
                print("未检测到视频")
        elif mode == '4':
            get_video_list(driver)
        elif mode == '5':
            get_next_unwatched_video(driver)
        elif mode == '6':
            jump_to_next_unwatched_video(driver)
        elif mode == '7':
            speed = input("请输入播放速度(0.5-4): ")
            set_speed(driver, speed)
        elif mode == '8':
            quality = input("请选择视频清晰度(1:高清 2:标清): ")
            quality = 'high' if quality == '1' else 'standard'
            set_video_quality(driver, quality)
        elif mode == '9':
            mute = input("是否静音(y/n): ")
            mute_video(driver)
        elif mode == '10':
            driver.refresh()
        elif mode == '11':
            try:
                time_str = input("请输入目标时间（格式：分:秒 或 秒数）: ")
                if ':' in time_str:
                    minutes, seconds = map(int, time_str.split(':'))
                    target_time = minutes * 60 + seconds
                else:
                    target_time = int(time_str)
                seek_video(driver, target_time)
            except ValueError:
                print("时间格式错误，请使用 分:秒 或 秒数")
        elif mode == 'q':
            print("退出手动模式")
            return

                
        # 继续监控
        time.sleep(1)
        manual_play(driver)
        
    except Exception as e:
        print(f"操作出错: {str(e)}")
        print("按车重试...")
        input()
        manual_play(driver)

def check_complete_button(driver):
    """检查'完成学习'按钮的状态"""
    try:
        button_status = driver.execute_script("""
            // 尝试多个选择器
            var button = document.querySelector('.contain-bottom .el-button') || 
                        document.querySelector('button.el-button--default') ||
                        document.querySelector('button.el-button');
                        
            if (!button) {
                console.log('未找到按钮');
                return null;
            }
            
            return {
                disabled: button.disabled || button.classList.contains('is-disabled'),
                className: button.className,
                text: button.textContent.trim(),
                isVisible: button.offsetParent !== null,
                element: button
            };
        """)
        
        if button_status is None:
            return 0
        if(button_status['disabled']):
            return 1
        else:
            return 2
        
    except Exception as e:
        print(f"检查按钮状态时出错: {str(e)}")
        return False

def click_complete_button(driver):
    """模拟人类点击完成学习按钮"""
    try:
        success = driver.execute_script("""
            function simulateHumanClick(element) {
                // 1. 滚动按钮到视图中心
                element.scrollIntoView({ behavior: 'smooth', block: 'center' });
                
                return new Promise(resolve => {
                    // 2. 等待滚动完成
                    setTimeout(() => {
                        // 3. 创建并触发鼠标移动事件
                        element.dispatchEvent(new MouseEvent('mouseover', {
                            bubbles: true,
                            cancelable: true,
                            view: window,
                            clientX: element.getBoundingClientRect().left + element.offsetWidth / 2,
                            clientY: element.getBoundingClientRect().top + element.offsetHeight / 2
                        }));
                        
                        // 4. 短暂延迟后触发鼠标按下事件
                        setTimeout(() => {
                            element.dispatchEvent(new MouseEvent('mousedown', {
                                bubbles: true,
                                cancelable: true,
                                view: window,
                                button: 0,
                                buttons: 1
                            }));
                            
                            // 5. 模拟点击一段时间后触发鼠标松开和点击事件
                            setTimeout(() => {
                                element.dispatchEvent(new MouseEvent('mouseup', {
                                    bubbles: true,
                                    cancelable: true,
                                    view: window,
                                    button: 0,
                                    buttons: 0
                                }));
                                
                                element.dispatchEvent(new MouseEvent('click', {
                                    bubbles: true,
                                    cancelable: true,
                                    view: window,
                                    button: 0,
                                    buttons: 0
                                }));
                                
                                resolve(true);
                            }, 50);  // 点击持续50ms
                        }, 100);  // 悬停100ms后点击
                    }, 500);  // 等待滚动完成
                });
            }
            
            // 查找按钮
            var button = document.querySelector('.contain-bottom .el-button') || 
                        document.querySelector('button.el-button--default') ||
                        document.querySelector('button.el-button');
                        
            if (!button) {
                console.log('未找到按钮');
                return { success: false, message: '未找到按钮' };
            }
            
            
            
            // 执行模拟人类点击
            return simulateHumanClick(button).then(() => ({
                success: true,
                message: '点击成功'
            }));
        """)
        
        if success.get('success'):
            print("完成按钮已点击")
            return True
        else:
            print(f"点击失败: {success.get('message', '未知错误')}")
            return False
            
    except Exception as e:
        print(f"点击按钮时出错: {str(e)}")

def control_video():

    driver = init()
    print("请选择运行模式：")
    print("1. 自动模式")
    print("2. 手动模式")
    mode = input("请输入选项：")

    if mode == '1':
        print("---------------------------------\n")
        auto_play(driver)
    elif mode == '2':
        print("---------------------------------\n")
        manual_play(driver)
    else:
        print("无效的选项，请重新选择")
        return
        
    

def get_chapters(driver):
    """获取章节列表"""
    try:
        chapters = driver.execute_script("""
            var chapters = [];
            // 获取所有章节元素
            var submenuList = document.querySelectorAll('.el-submenu');
            
            submenuList.forEach(function(submenu) {
                var chapterTitle = submenu.querySelector('.el-submenu__title .of_eno').textContent.trim();
                var sections = [];
                
                // 获取每个章节下的小节
                var menuItems = submenu.querySelectorAll('.el-menu-item .of_eno');
                menuItems.forEach(function(item) {
                    sections.push({
                        title: item.textContent.trim(),
                        element: item.closest('.el-menu-item')
                    });
                });
                
                chapters.push({
                    title: chapterTitle,
                    sections: sections
                });
            });
            
            return chapters;
        """)
        
        # 打印章节结构
        for i, chapter in enumerate(chapters, 1):
            print(f"{chapter['title']}")
            for j, section in enumerate(chapter['sections'], 1):
                print(f"  {j}. {section['title']}")
                
        return chapters
        
    except Exception as e:
        print(f"获取章节列表时出错: {str(e)}")
        return None

def click_chapter(driver, chapter_index, section_index):

    try:
        success = driver.execute_script("""
            function clickElement(element) {
                // 创建点击事件
                var event = new MouseEvent('click', {
                    bubbles: true,
                    cancelable: true,
                    view: window
                });
                element.dispatchEvent(event);
            }
            
            var submenuList = document.querySelectorAll('.el-submenu');
            if (!submenuList.length) return false;
            
            var chapter = submenuList[arguments[0] - 1];
            if (!chapter) return false;
            
            // 如果章节是折叠的，先展开
            if (!chapter.classList.contains('is-opened')) {
                clickElement(chapter.querySelector('.el-submenu__title'));
                // 等待展开动画
                await new Promise(resolve => setTimeout(resolve, 300));
            }
            
            // 点击指定小节
            var menuItems = chapter.querySelectorAll('.el-menu-item');
            var section = menuItems[arguments[1] - 1];
            if (!section) return false;
            
            clickElement(section);
            return true;
        """, chapter_index, section_index)
        
        if success:
            print(f"已点击第{chapter_index}章第{section_index}节")
        else:
            print("点击失败：未找到指定章节")
            
    except Exception as e:
        print(f"点击章节出错: {str(e)}")

# 使用示例：
def get_video_list(driver):
    """获取视频列表及其学习状态"""
    try:
        videos = driver.execute_script("""
            var videos = [];
            // 获取所有视频标签
            var items = document.querySelectorAll('.el-tabs__item');
            
            items.forEach(function(item) {
                try {
                    var icon = item.querySelector('.label i');  // 修改选择器
                    var titleSpan = item.querySelector('.label span:last-child');  // 修改选择器
                    
                    if (!titleSpan) return;  // 跳过无标题的项
                    
                    var title = titleSpan.textContent.trim();
                    
                    // 检查学习状态
                    var status = 'not_started';  // 默认未开始
                    if (icon) {
                        if (icon.classList.contains('complete')) {
                            status = 'completed';
                        } else if (icon.classList.contains('no-start')) {
                            status = 'not_started';
                        } else if (icon.classList.contains('icon-iconset0387')) {
                            status = 'other';
                        }
                    }
                    
                    videos.push({
                        title: title,
                        status: status,
                        element: item,
                        id: item.id
                    });
                } catch (e) {
                    console.log('处理视频项时出错:', e);
                }
            });
            
            return videos;
        """)
        
        if not videos:
            print("未找到任何视频")
            return None
        
        x = 0
        for i, video in enumerate(videos, 1):
            status_text = {
                'completed': '✅ 已完成',
                'not_started': '❌ 未开始',
                'other': '⚠️ 其他'
            }.get(video['status'], '未知态')
            
            print(f"{i}. {status_text} | {video['title']}")
            if video['status'] == 'not_started':
                x += 1
        
        
        if x == 0:
            #print("所有节点都已完成")
            return None
        else:
            print(f"发现{x}个未完成节点")
            
        return videos
        
    except Exception as e:
        print(f"获取视频列表时出错: {str(e)}")
        return None

def get_next_unwatched_video(driver):
    """获取下一个未看的视频"""
    try:
        video = driver.execute_script("""
            var items = document.querySelectorAll('.el-tabs__item');
            for (var item of items) {
                var icon = item.querySelector('i');
                // 找到第一个不含complete类的视频
                if (icon && !icon.classList.contains('complete')) {
                    return {
                        title: item.querySelector('span.label > span').textContent.trim(),
                        element: item
                    };
                }
            }
            return null;
        """)
        
        if video:
            print(f"\n找到未完成的视频: {video['title']}")
            return video
        else:
            print("所有视频都完成！")
            return None
            
    except Exception as e:
        print(f"查找未完成视频时出错: {str(e)}")
        return None

def jump_to_next_unwatched_video(driver):
    """跳转到下一个未学习的视频"""
    try:
        result = driver.execute_script("""
            function getVideoStatus(item) {
                var icon = item.querySelector('.label i');
                if (!icon) return 'unknown';
                
                if (icon.classList.contains('complete')) {
                    return 'completed';
                } else if (icon.classList.contains('no-start')) {
                    return 'not_started';
                } else if (icon.classList.contains('icon-iconset0387')) {
                    return 'other';
                }
                return 'not_started';  // 默认开始
            }
            
            // 获取所有视频标签
            var items = Array.from(document.querySelectorAll('.el-tabs__item'));
            if (!items.length) {
                console.log('未找到视频列表');
                return { success: false, message: '未找到视频列表' };
            }
            
            // 找到当前激活的视频
            var currentIndex = items.findIndex(item => item.classList.contains('is-active'));
            console.log('找到的视频数量:', items.length);
            console.log('当前视频索引:', currentIndex);
            
            // 从当前视频的下一个开始查找未完成的视频
            var startIndex = currentIndex === -1 ? 0 : currentIndex + 1;
            
            // 查找下一个完成的视频
            for (var i = startIndex; i < items.length; i++) {
                var item = items[i];
                var status = getVideoStatus(item);
                var titleSpan = item.querySelector('.label span:last-child');
                
                if (!titleSpan) continue;  // 跳过无标题的项
                
                var title = titleSpan.textContent.trim();
                console.log(`检查视频 [${i}]: ${title} (${status})`);
                
                if (status !== 'completed') {
                    // 找到未完成的视频，尝试点击
                    try {
                        item.scrollIntoView({ behavior: 'smooth', block: 'center' });
                        await new Promise(resolve => setTimeout(resolve, 500));
                        item.click();
                        
                        return {
                            success: true,
                            title: title,
                            index: i,
                            status: status
                        };
                    } catch (e) {
                        console.log('点击失败:', e);
                        continue;
                    }
                }
            }
            
            return { 
                success: false, 
                message: '没有找到更多未完成的视频' 
            };
        """)
        
        if result.get('success'):
            status_text = {
                'not_started': '未开始',
                'other': '其他状态',
                'unknown': '未知状态'
            }.get(result.get('status'), '未完成')
            
            print(f"\n已跳转到下一个未完成节点:{result['title']}")
            
            
            
            # 等待新视频加载
            time.sleep(2)
            return True
        else:
            print(f"\n{result.get('message', '跳转失败')}")
            return False
            
    except Exception as e:
        print(f"跳转时出错: {str(e)}")
        return False

def read_config():
    """读取配置文件"""
    try:
        with open('config.txt', 'r', encoding='utf-8') as f:
            lines = f.readlines()
            if len(lines) >= 3:  # 修改为至少3行
                username = lines[0].strip()
                password = lines[1].strip()
                driver_path = lines[2].strip()
                return username, password, driver_path
            else:
                print("配置文件格式错误，请确保config.txt包含：")
                print("第1行：用户名")
                print("第2行：密码")
                print("第3行：浏览器驱动程序路径")
                return None, None, None
    except FileNotFoundError:
        print("未找到config.txt文件，请创建文件并填写配置信息")
        return None, None, None
    except Exception as e:
        print(f"读取配置文件时出错: {str(e)}")
        return None, None, None

def set_video_quality(driver, quality='high'):
    """设置视频清晰度
    quality: 'high' (高清) 或 'standard' (标清)
    """
    try:
        success = driver.execute_script("""
            function setQuality(targetQuality) {
                // 查找清晰度设置按钮
                var settingsButton = document.querySelector('.definitionchsdwogjayml');
                if (!settingsButton) {
                    console.log('未找到清晰度设置按钮');
                    return false;
                }
                
                // 点击设置按钮
                settingsButton.click();
                
                // 等待选项出现
                return new Promise(resolve => {
                    setTimeout(() => {
                        try {
                            // 根据当前文本判断是否需要切换
                            var currentQuality = settingsButton.textContent.trim();
                            var needSwitch = (targetQuality === 'high' && currentQuality !== '高清') ||
                                           (targetQuality === 'standard' && currentQuality !== '标清');
                            
                            if (needSwitch) {
                                // 再次点击切换清晰度
                                settingsButton.click();
                                console.log('切换清晰度');
                                resolve(true);
                            } else {
                                console.log('当前已是目标清晰度');
                                resolve(true);
                            }
                        } catch (e) {
                            console.log('设置清晰度失败:', e);
                            resolve(false);
                        }
                    }, 500);
                });
            }
            
            return setQuality(arguments[0]);
        """, quality)
        
        if success:
            print(f"已设置视频清晰度为: {'高清' if quality == 'high' else '标清'}")
        else:
            print("设置视频清晰度失败")
            
    except Exception as e:
        print(f"设置视频清晰度时出错: {str(e)}")

def seek_video(driver, time_in_seconds):
    """跳转到指定时间
    time_in_seconds: 目标时间（秒）
    """
    try:
        result = driver.execute_script("""
            function seekTo(targetTime) {
                var video = document.querySelector('video');
                if (!video) {
                    return { success: false, message: '未找到视频' };
                }
                
                // 检查时间是否有效
                if (targetTime < 0 || targetTime > video.duration) {
                    return { 
                        success: false, 
                        message: `时间超出范围 (0-${Math.floor(video.duration)}秒)`
                    };
                }
                
                try {
                    // 保存当前播放状态
                    var wasPlaying = !video.paused;
                    
                    // 设置时间
                    video.currentTime = targetTime;
                    
                    // 如果之前在播放，继续播放
                    if (wasPlaying) {
                        video.play();
                    }
                    
                    return {
                        success: true,
                        currentTime: video.currentTime,
                        duration: video.duration
                    };
                } catch (e) {
                    return { success: false, message: '跳转失败: ' + e.message };
                }
            }
            
            return seekTo(arguments[0]);
        """, time_in_seconds)
        
        if result.get('success'):
            print(f"已跳转到: {int(result['currentTime'])}/{int(result['duration'])}秒")
            return True
        else:
            print(f"跳转失败: {result.get('message', '未知错误')}")
            return False
            
    except Exception as e:
        print(f"跳转时出错: {str(e)}")
        return False

if __name__ == "__main__":
    control_video()