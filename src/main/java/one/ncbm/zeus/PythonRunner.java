package one.ncbm.zeus;
import java.io.Closeable;
import java.util.concurrent.BlockingQueue;
import java.util.concurrent.LinkedBlockingQueue;
import java.util.function.Consumer;

import org.slf4j.Logger;

import com.mojang.logging.LogUtils;

import jep.Interpreter;
import jep.SharedInterpreter;

public class PythonRunner implements Closeable {
    private final BlockingQueue<Consumer<Interpreter>> taskQueue = new LinkedBlockingQueue<>();
    private volatile boolean running = true;
    private static final Logger LOGGER = LogUtils.getLogger();
    private volatile Thread thread;

    public PythonRunner() {
        thread = new Thread(() -> {
            Interpreter interp = new SharedInterpreter(); 
            while (running) {
                try {
                    Consumer<Interpreter> task = taskQueue.take();
                    task.accept(interp);
                } catch (InterruptedException e) {
                    LOGGER.warn("Interpreter queue interrupted.");
                }
            }
            interp.close();
        });
        thread.start();
    }

    public void execute(Consumer<Interpreter> task) {
        if (!running) {
            throw new IllegalStateException("Interpreter queue is not running.");
        }
        taskQueue.add(task);
    }

    public void close() {
        running = false;
        taskQueue.clear();
    }
}
