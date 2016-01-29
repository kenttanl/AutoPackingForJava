# 根据SVN增量补丁日志，自动生成补丁包
import tkinter.filedialog as tkFD
import os, shutil, time, sys
from tkinter.filedialog import askopenfilename
from tkinter import *

# 允许的文件扩展名
FILTER_EXTEN = ['.java', '.class', '.xml', '.properties', '.jsp', '.js', '.html']

# 目标文件夹生产过滤（比如WebRoot目录是不需要的）
FILTER_TARGET_DIR = ['WebRoot/']

# 补丁生成路径
PATCH_GENERATE_PATH = ''

# 补丁包名称
PATCH_NAME = ''

# 异常
IS_EXCEPTION = False

# -------------------- 以下属性由配置文件读出 --------------------
# SVN补丁日志文件默认位置
DEFAULT_SVN_LOG_PATH = ''

# 是否使用SVN补丁日志文件默认位置
IS_DEFAULT_SVN_LOG_PATH = 0

# 工作空间默认位置，可为空
DEFAULT_WORKSPACE_PATH = ''

# 是否使用工作空间默认位置
IS_DEFAULT_WORKSPACE_PATH = 0

# 是否自动生成补丁包名称
IS_AUTO_GENERATE_PATCHNAME = 1


# 创建一个补丁生成类
class Patch():
    patchFile           = ''
    projectName         = ''
    projectPath         = ''
    patchFileList       = []  # 补丁文件列表
    filterPatchFileList = []  # 被过滤的文件列表
    patchLog            = []  # 日志信息列表
    
    # 构造函数
    def __init__(self):
        # 解析配置文件
        self.parseConfigFile()

        # print(DEFAULT_SVN_LOG_PATH)
        # print(IS_DEFAULT_SVN_LOG_PATH)
        # print(DEFAULT_WORKSPACE_PATH)
        # print(IS_DEFAULT_WORKSPACE_PATH)
        # pass

    # 开始打补丁
    def start(self):
        # 选择SVN补丁日志文件
        self.selectFile()
        # 生成补丁包名称
        self.generatePatchName()
        # 解析文件
        self.parseSvnPatchFile()
        # 打印补丁包信息
        self.printPatchFile()
        # 生成补丁包
        self.generatePatch()

    # 选择文件
    def selectFile(self):
        global IS_DEFAULT_SVN_LOG_PATH
        global DEFAULT_SVN_LOG_PATH

        # 根据配置文件中的信息，判断是否需要使用默认的地址
        if IS_DEFAULT_SVN_LOG_PATH != '1':
            root = Tk()
            root.withdraw()
            self.patchFile = tkFD.askopenfilename(defaultextension=".txt",initialdir="/home/",title="选择SVN补丁文件")
        else:
            self.patchFile = DEFAULT_SVN_LOG_PATH

    # 解析SVN补丁日志文件
    def parseSvnPatchFile(self):
        global FILTER_EXTEN


        print(self.patchFile)
        
        # 如果文件不存在
        if not os.path.exists(self.patchFile):
            self.patchLog.append('\r\n')
            self.patchLog.append(' >> 不存在的SVN补丁日志文件：' + self.patchFile)
            print(' >> 不存在的SVN补丁日志文件：' + self.patchFile)
            IS_EXCEPTION = True
            return
        
        patchFile = open(self.patchFile, 'r')

        '''
        # SVN补丁文件规则描述（仅目前所知，非正规文档描述）
        # 对于有修改或增加的文件，大致为如下格式(0, 1， 2， 3行)：
        0 Index: src/gnnt/service/ApplyAndAuditService.java
        1 ===================================================================
        2 --- src/gnnt/service/ApplyAndAuditService.java	(revision 9003)
        3 +++ src/gnnt/service/ApplyAndAuditService.java	(working copy)
        4 ...
        # 将根据以上规则获取增量文件名
        '''
        prepare          = False  # 准备阶段
        possibleFilename = '' # 可能的文件名
        
        for line in patchFile.readlines():
            
            # 解析被记录的文件
            prefixIden = line[0: 6]  # 获取前6个字符
            if prefixIden == 'Index:':
                line = line.replace('\t', ' ')         # 将制表符转换为空格
                line = line.replace('\n', '')         # 将换行符去掉
                lineList = line.split(' ')
                if len(lineList) >= 2:
                    possibleFilename = lineList[1]
                    
                    # 保留java源文件
                    oldFilename = possibleFilename;
                    
                    # 将java文件替换成class文件
                    possibleFilename = possibleFilename.replace('src/', 'WebRoot/WEB-INF/classes/')
                    possibleFilename = possibleFilename.replace('.java', '.class')

                    self.addPatchFile(possibleFilename)

                    # 保留java源文件
                    if oldFilename != possibleFilename:
                        self.addPatchFile(oldFilename)
                    
                continue

            # 解析项目名称
            prefixIden = line[0: 2]  # 获取前2个字符
            if prefixIden == '#P':
                lineList = line.split(' ')
                if len(lineList) >= 2:
                    self.projectName = lineList[1].replace('\n', '')
                    # print()
                    # print('解析到的项目名称：', self.projectName)
                    self.patchLog.append('\n')
                    self.patchLog.append('解析到的项目名称：' + self.projectName)
            
            
            """ 保留但先暂时不使用以下方式解析被修改的补丁文件
            if prefixIden == '===':
                prepare = True
                continue

            if prepare == True and prefixIden == '---':
                line = line.replace('\t', ' ')         # 将制表符转换为空格
                lineList = line.split(' ')
                if len(lineList) > 2:
                    possibleFilename = lineList[1]
                    # print(len(lineList))
                    # print(possibleFilename)
                    continue

            if prepare == True and prefixIden == '+++':
                line = line.replace('\t', ' ')         # 将制表符转换为空格
                lineList = line.split(' ')
                if len(lineList) > 2:
                    if lineList[1] == possibleFilename:
                        self.patchFileList.append(possibleFilename)
                    else:
                        possibleFilename = ''
            """
            
            # print(prefixIden)

        # print(self.patchFileList)
        patchFile.close()

    # 添加文件至解析完成的补丁文件
    def addPatchFile(self, patchFilename):
        isAllow = False
        for exten in FILTER_EXTEN:
            if patchFilename[0 - len(exten):] == exten:
                isAllow = True
                continue
                    
        if not isAllow:
            # self.patchLog.append('被过滤的文件：' + patchFilename)
            self.filterPatchFileList.append(patchFilename)
        else:
            self.patchFileList.append(patchFilename)
    

    # 生成补丁包
    def generatePatch(self):
        global PATCH_GENERATE_PATH
        global FILTER_TARGET_DIR
        global PATCH_NAME
        global IS_DEFAULT_WORKSPACE_PATH
        global DEFAULT_WORKSPACE_PATH

        # 设置项目地址
        if IS_DEFAULT_WORKSPACE_PATH != '1':
            projectPath = tkFD.askdirectory(initialdir="/home/",title="选择工作空间") + '/' + self.projectName
        else:
            projectPath = DEFAULT_WORKSPACE_PATH + '/' + self.projectName

        self.projectPath = projectPath
        
        # 补丁生产目录添加上补丁名称与项目名称
        if (PATCH_GENERATE_PATH == ''):
            patchDir = PATCH_NAME + self.projectName + "/"
        else:
            patchDir = PATCH_NAME + PATCH_GENERATE_PATH + '/' + self.projectName + "/"

        # print()
        # print('补丁包生成详细信息：')
        self.patchLog.append('\r\n')
        self.patchLog.append('补丁包生成详细信息：')
        for patchFile in self.patchFileList:
            targetPatchFile = patchFile
            
            # 将目标文件夹中不需要的文件夹名称去掉
            for filterDir in FILTER_TARGET_DIR:
                if patchFile[:len(filterDir)] == filterDir:
                    targetPatchFile = patchFile[len(filterDir):]    # 目标文件位置
            
            dirList = targetPatchFile.split('/')
            targetDirPath = targetPatchFile[0: len(targetPatchFile) - len(dirList[len(dirList) - 1])]
            
            # 如果源文件存在
            if os.path.exists(projectPath + '/' + patchFile):
                # 如果目录不存在则创建目录
                if os.path.exists(patchDir + targetDirPath) == False:
                    os.makedirs(patchDir + targetDirPath)
                    # print('  >> 创建目录： ' + patchDir + targetDirPath)
                    self.patchLog.append('  >> 创建目录：' + self.projectName + '/' + targetDirPath)  # patchDir

                # 拷贝文件
                shutil.copyfile(projectPath + '/' + patchFile,  patchDir + targetPatchFile)

                # print('  >> 拷贝文件：', projectPath)
                self.patchLog.append('  >> 拷贝文件：' + projectPath + '/' + patchFile)
            else:
                # print('  >> 不存在的：', projectPath + '/' + patchFile)
                self.patchLog.append('  >> 不存在的：' + projectPath + '/' + patchFile)

        self.projectPath = projectPath
    
    # 打印解析到的补丁文件
    def printPatchFile(self):
        # print()
        # print("-----------------------------------补丁包文件-----------------------------------")
        # print('解析到的补丁文件：')
        self.patchLog.append('\r\n')
        self.patchLog.append('解析到的补丁文件：')
        for filename in self.patchFileList:
            # print('  >>', filename)
            self.patchLog.append('  >>' + filename)
        # print("--------------------------------------------------------------------------------")

        self.patchLog.append('\r\n')
        self.patchLog.append('被过滤的补丁文件：')
        for filename in self.filterPatchFileList:
            self.patchLog.append('  >>' + filename)

    # 获取补丁名称
    def inputPatchName(self):
        global PATCH_NAME
        
        patchName = input("请输入补丁名称:")

        if (patchName != ''):
            patchName = patchName + '/'

        PATCH_NAME = patchName

    # 解析配置文件
    def parseConfigFile(self):
        global DEFAULT_SVN_LOG_PATH
        global IS_DEFAULT_SVN_LOG_PATH
        global DEFAULT_WORKSPACE_PATH
        global IS_DEFAULT_WORKSPACE_PATH
        
        configFile = open('config.properties')

        for line in configFile.readlines():
            line = line.replace('\t', ' ')         # 将制表符转换为空格
            line = line.replace('\n', '')          # 将换行符去掉

            if len(line) > 0:
                # 判断是否为注释
                prefixIden = line[0 : 1]
                if prefixIden == '#':
                    continue

                # 获取属性
                if '=' in line:
                    attrMap = line.split('=')
                    if len(attrMap) >= 2:
                        key   = attrMap[0]    # 获取键
                        value = attrMap[1]  # 获取值

                        if key == 'DEFAULT_SVN_LOG_PATH':
                            DEFAULT_SVN_LOG_PATH = value
                        elif key == 'IS_DEFAULT_SVN_LOG_PATH':
                            IS_DEFAULT_SVN_LOG_PATH = value
                        elif key == 'DEFAULT_WORKSPACE_PATH':
                            DEFAULT_WORKSPACE_PATH = value
                        elif key == 'IS_DEFAULT_WORKSPACE_PATH':
                            IS_DEFAULT_WORKSPACE_PATH = value
                        elif key == 'IS_AUTO_GENERATE_PATCHNAME':
                            IS_AUTO_GENERATE_PATCHNAME = value
            configFile.close()
        # pass

    # 生成补丁包名称
    def generatePatchName(self):
        global IS_AUTO_GENERATE_PATCHNAME
        global PATCH_NAME
        
        patchName = ''
        
        if IS_AUTO_GENERATE_PATCHNAME == 1:
            patchnameList = []
            nowDate   = time.strftime('%Y%m%d', time.gmtime(time.time()))
            # 遍历当前目录
            pathDir = os.listdir('./')
            for pdir in pathDir:
                if pdir[0: len(nowDate)] == nowDate:
                    patchnameList.append(pdir[len(nowDate):])
                    # print(pdir[len(nowDate):])

            temp = 0
            for patchname in patchnameList:
                if int(patchname) > temp:
                    temp = int(patchname)
            
            PATCH_NAME = nowDate + ('%05d' %(temp + 1)) + '/'
            
        else:
            self.inputPatchName()

    # 生成日志
    def generateLog(self):
        if not IS_EXCEPTION:
            if os.path.exists(PATCH_GENERATE_PATH + PATCH_NAME) == False:
                    os.makedirs(PATCH_GENERATE_PATH + PATCH_NAME)
                    
            logFile = open(PATCH_GENERATE_PATH + PATCH_NAME + 'log.txt', 'w')

            for log in self.patchLog:
                logFile.write(log)
                logFile.write('\r\n')

                time.sleep(0.01)
            
                print(log)

            logFile.close()

            print('  >> 生成文件：补丁日志文件完成')

def cur_file_dir():
     #获取脚本路径
     path = sys.path[0]

     #判断为脚本文件还是py2exe编译后的文件，如果是脚本文件，则返回的是脚本的目录，如果是py2exe编译后的文件，则返回的是编译后的文件路径
     if os.path.isdir(path):
         return path
     elif os.path.isfile(path):
         return os.path.dirname(path)
 

if __name__ == "__main__":
    print()
    print("正在生成补丁...")
    print()
    print("正在解析文件...")
    
    patch = Patch()
    patch.start()

    patch.generateLog()

    if not IS_EXCEPTION:
        print()
        print('生成补丁包完成：')
        print('  >> 补丁包名称：', PATCH_NAME[0: -1])
        print('  >> 补丁包路径：', cur_file_dir().replace('\\', '/') + '/' + PATCH_NAME)
    
    # input()
    print()
    os.system("pause")
    
