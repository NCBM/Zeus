package one.ncbm.zeus;

import java.io.File;
import java.util.Arrays;

import org.slf4j.Logger;

import com.mojang.logging.LogUtils;

public class PythonRuntimeManager {
    private static final Logger LOGGER = LogUtils.getLogger();
    private static final String osName = System.getProperty("os.name");
    private static final String osVersion = System.getProperty("os.version");
    private static final String pyHome = getPythonHome();

    public static String getPythonHome() {
        File pythonHome = new File("python/");
        if (!pythonHome.isDirectory()) {
            String envPythonHome = System.getenv("PYTHON_HOME");
            if (envPythonHome == null) {
                return null;
            }
            pythonHome = new File(envPythonHome);
            if (!pythonHome.isDirectory()) {
                if (pythonHome.exists()) {
                    throw new RuntimeException("Current python home is not a directory.");
                }
                return null;
            }
        }
        return pythonHome.getAbsolutePath();
    }

    public static String getPythonModuleRoot() {
        File pyRoot;
        if (osName == null || osVersion == null) {
            throw new RuntimeException("Cannot get operating system name and version.");
        }
        if (osName.contains("Windows")) {
            pyRoot = new File(pyHome + "/Lib/");
            double osVer = Double.parseDouble(osVersion);
            if (osVer < 10) {
                LOGGER.warn("Your system version is lower than Windows 10, thus running this mod may came to error. We are not responsible for this kind of issues.");
            }
        } else {
            File pyLib = new File(pyHome + "/lib");
            String[] _pyLibs = pyLib.list((file, name) -> name.startsWith("python3."));
            if (_pyLibs == null) {
                throw new RuntimeException("Cannot find python module root.");
            }
            Arrays.sort(_pyLibs, (a, b) -> {
                if (a.length() != b.length()) {
                    return Integer.valueOf(b.length()).compareTo(a.length());
                }
                return b.compareTo(a);
            });
            String pyName = Arrays.stream(_pyLibs).findFirst().orElseThrow();
            pyRoot = new File(pyHome + "/lib/" + pyName + "/");
        }
        if (!pyRoot.isDirectory()) {
            throw new RuntimeException("Cannot find python module root.");
        }
        return pyRoot.getAbsolutePath();
    }

    public static String getJepLibPath() {
        File libjep;
        String jepBase = getPythonModuleRoot();
        if (osName == null || osVersion == null) {
            throw new RuntimeException("Cannot get operating system name and version.");
        }
        if (osName.contains("Windows")) {
            libjep = new File(jepBase + "/site-packages/jep/libjep.pyd");
        } else if (osName.contains("macOS") || osName.contains("Mac OS")) {
            libjep = new File(jepBase + "/site-packages/jep/libjep.dylib");
        } else {
            libjep = new File(jepBase + "/site-packages/jep/libjep.so");
        }
        if (!libjep.isFile()) {
            throw new RuntimeException("Cannot find libjep.");
        }
        return libjep.getAbsolutePath();
    }

    public static void downloadPythonRuntime() {}
}
