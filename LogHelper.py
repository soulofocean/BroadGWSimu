# coding
import logging
import os
import traceback


class LogHelper:
    def __init__(self, fullName, clevel=logging.INFO, cenable=True, flevel=logging.INFO, fenable=True, encode='utf-8',
                 endline=''):
        # CommonIF.get_log_full_name(file_prefix=fullName, file_ext=".log")
        self.fullName = fullName
        self.logDir = os.path.dirname(self.fullName)
        if not self.logDir:
            self.logDir = os.path.curdir
        os.makedirs(self.logDir, exist_ok=True)
        self.p = logging.getLogger(self.fullName)
        self.endLine = endline

        # 清除掉所有Handler防止输出多行LOG
        self.p.handlers.clear()
        self.p.setLevel(logging.DEBUG)
        # fmt = logging.Formatter('[%(asctime)s] [%(levelname)s] %(message)s', '%m-%d %H:%M:%S')
        self.fmt = logging.Formatter(
            fmt='[%(asctime)10s.%(msecs)03d]%(message)s',
            datefmt="%F %T")

        # 设置CMD日志
        if cenable:
            self.sh = logging.StreamHandler()
            self.sh.setFormatter(self.fmt)
            self.sh.setLevel(clevel)
            self.p.addHandler(self.sh)

        # 设置文件日志
        if fenable:
            self.fh = logging.FileHandler(self.fullName, encoding=encode)
            self.fh.setFormatter(self.fmt)
            self.fh.setLevel(flevel)
            self.p.addHandler(self.fh)

    def set_level(self, clevel=logging.DEBUG):
        self.critical('Change log level to %s' % (str(clevel)))
        self.p.setLevel(clevel)

    def debug(self, message):
        s = traceback.extract_stack()
        message = str(message)
        message += self.endLine
        self.p.debug("[{:5s}][{}:{:3d}]{}".format("DEBUG", os.path.basename(s[-2][0]), s[-2][1], message))

    def info(self, message):
        s = traceback.extract_stack()
        message = str(message)
        message += self.endLine
        self.p.info("[{:5s}][{}:{:3d}]{}".format("INFO", os.path.basename(s[-2][0]), s[-2][1], message))

    def warn(self, message):
        s = traceback.extract_stack()
        message = str(message)
        message += self.endLine
        self.p.warning("[{:5s}][{}:{:3d}]{}".format("WARN", os.path.basename(s[-2][0]), s[-2][1], message))

    def error(self, message):
        s = traceback.extract_stack()
        message = str(message)
        # message += self.endLine
        self.p.error("[{:5s}][{}:{:3d}]{}".format("ERROR", os.path.basename(s[-2][0]), s[-2][1], message))

    def critical(self, message):
        """为了兼容模拟器之前的调用"""
        self.fatal(message)

    def yinfo(self, message):
        self.info(message)

    def fatal(self, message):
        s = traceback.extract_stack()
        message = str(message)
        message += self.endLine
        self.p.critical("[{:5s}][{}:{:3d}]{}".format("FATAL", os.path.basename(s[-2][0]), s[-2][1], message))


if __name__ == '__main__':
    # start = time.time()
    # b = BasicCaseResultType("ID1")
    # print(b.load_detail_log())
    # print(time.time()-start)
    # exit(666)
    loghelper = LogHelper("log/zx3")
    # l = LogHelper(".\\log_folder\\zx.txt")
    # l.set_level(logging.CRITICAL)
    loghelper.debug("debug")
    loghelper.info("info")
    loghelper.warn("warn")
    loghelper.error("error")
    loghelper.critical("critical")
    loghelper.fatal("fatal")
