package one.ncbm.zeus;

import java.io.File;

// import org.apache.logging.log4j.core.config.builder.api.Component;
import org.slf4j.Logger;

import com.mojang.logging.LogUtils;

import jep.MainInterpreter;
import jep.PyConfig;
import net.minecraft.client.Minecraft;
import net.minecraft.core.registries.BuiltInRegistries;
import net.minecraft.world.food.FoodProperties;
import net.minecraft.world.item.BlockItem;
import net.minecraft.world.item.CreativeModeTab;
import net.minecraft.world.item.CreativeModeTabs;
import net.minecraft.world.item.Item;
import net.minecraft.world.level.block.Block;
import net.minecraft.world.level.block.Blocks;
import net.minecraft.world.level.block.state.BlockBehaviour;
import net.minecraft.world.level.material.MapColor;
import net.neoforged.api.distmarker.Dist;
import net.neoforged.bus.api.IEventBus;
import net.neoforged.bus.api.SubscribeEvent;
import net.neoforged.fml.ModContainer;
import net.neoforged.fml.common.EventBusSubscriber;
import net.neoforged.fml.common.Mod;
import net.neoforged.fml.config.ModConfig;
import net.neoforged.fml.event.lifecycle.FMLClientSetupEvent;
import net.neoforged.fml.event.lifecycle.FMLCommonSetupEvent;
import net.neoforged.neoforge.common.NeoForge;
import net.neoforged.neoforge.event.BuildCreativeModeTabContentsEvent;
import net.neoforged.neoforge.event.GameShuttingDownEvent;
import net.neoforged.neoforge.event.server.ServerStartingEvent;
import net.neoforged.neoforge.registries.DeferredBlock;
import net.neoforged.neoforge.registries.DeferredHolder;
import net.neoforged.neoforge.registries.DeferredItem;
import net.neoforged.neoforge.registries.DeferredRegister;

// The value here should match an entry in the META-INF/neoforge.mods.toml file
@Mod(ZeusMain.MODID)
public class ZeusMain
{
    public static final String MODID = "zeus";
    private static final Logger LOGGER = LogUtils.getLogger();

    public static final Registry registry = new Registry();
    public PythonRunner pythonRunner;
    // private Object server;

    public static final DeferredRegister.Blocks BLOCKS = Registry.BLOCKS;
    public static final DeferredRegister.Items ITEMS = Registry.ITEMS;
    public static final DeferredRegister<CreativeModeTab> CREATIVE_MODE_TABS = Registry.CREATIVE_MODE_TABS;

    public static final DeferredBlock<Block> EXAMPLE_BLOCK = BLOCKS.registerSimpleBlock("example_block", BlockBehaviour.Properties.of().mapColor(MapColor.STONE));
    public static final DeferredItem<BlockItem> EXAMPLE_BLOCK_ITEM = ITEMS.registerSimpleBlockItem("example_block", EXAMPLE_BLOCK);

    public static final DeferredItem<Item> EXAMPLE_ITEM = ITEMS.registerSimpleItem("example_item", new Item.Properties().food(new FoodProperties.Builder()
            .alwaysEdible().nutrition(1).saturationModifier(2f).build()));

    public static final DeferredHolder<CreativeModeTab, CreativeModeTab> EXAMPLE_TAB = Registry.creativeModeTabBefore(
        "example_tab", "itemGroup.zeus", EXAMPLE_ITEM, (parameters, output) -> {
            output.accept(EXAMPLE_ITEM.get());
        }, CreativeModeTabs.COMBAT);

    // The constructor for the mod class is the first code that is run when your mod is loaded.
    // FML will recognize some parameter types like IEventBus or ModContainer and pass them in automatically.
    public ZeusMain(IEventBus modEventBus, ModContainer modContainer)
    {
        File pyhome = new File("python/");
        File libjep = new File("python/lib/python3.13/site-packages/jep/libjep.so");
        PyConfig config = new PyConfig();
        config.setPythonHome(pyhome.getAbsolutePath());
        
        try {
            MainInterpreter.setJepLibraryPath(libjep.getAbsolutePath());
            MainInterpreter.setInitParams(config);
            pythonRunner = new PythonRunner();
            pythonRunner.execute((interpreter) -> {
                interpreter.exec("import importlib");
                interpreter.exec("import sys");
                interpreter.exec("import os");
                interpreter.exec("sys.path.insert(0, \"python/mods\")");
                interpreter.exec("for mod in os.listdir('python/mods'):\n    if mod.startswith('_'): continue\n    importlib.import_module(mod)");
            });
        } catch (Exception e) {
            LOGGER.error("Cannot start python interpreter for mod '{}'.", MODID, e);
            throw e;
        }

        // Register the commonSetup method for modloading
        modEventBus.addListener(this::commonSetup);

        BLOCKS.register(modEventBus);
        ITEMS.register(modEventBus);
        CREATIVE_MODE_TABS.register(modEventBus);

        // Register ourselves for server and other game events we are interested in.
        // Note that this is necessary if and only if we want *this* class (ExampleMod) to respond directly to events.
        // Do not add this line if there are no @SubscribeEvent-annotated functions in this class, like onServerStarting() below.
        NeoForge.EVENT_BUS.register(this);

        // Register the item to a creative tab
        modEventBus.addListener(this::addCreative);

        // Register our mod's ModConfigSpec so that FML can create and load the config file for us
        modContainer.registerConfig(ModConfig.Type.COMMON, Config.SPEC);
    }

    private void commonSetup(final FMLCommonSetupEvent event)
    {
        // Some common setup code
        LOGGER.info("HELLO FROM COMMON SETUP");

        if (Config.logDirtBlock)
            LOGGER.info("DIRT BLOCK >> {}", BuiltInRegistries.BLOCK.getKey(Blocks.DIRT));

        LOGGER.info(Config.magicNumberIntroduction + Config.magicNumber);

        Config.items.forEach((item) -> LOGGER.info("ITEM >> {}", item.toString()));
    }

    // Add the example block item to the building blocks tab
    private void addCreative(BuildCreativeModeTabContentsEvent event)
    {
        if (event.getTabKey() == CreativeModeTabs.BUILDING_BLOCKS)
            event.accept(EXAMPLE_BLOCK_ITEM);
    }

    // You can use SubscribeEvent and let the Event Bus discover methods to call
    @SubscribeEvent
    public void onServerStarting(ServerStartingEvent event)
    {
        // Do something when the server starts
        LOGGER.info("HELLO from server starting");
    }

    @SubscribeEvent
    public void onShutdown(GameShuttingDownEvent event) {
        pythonRunner.execute((interpreter) -> {
            interpreter.exec("");
        });
        pythonRunner.close();
    }

    // You can use EventBusSubscriber to automatically register all static methods in the class annotated with @SubscribeEvent
    @EventBusSubscriber(modid = MODID, bus = EventBusSubscriber.Bus.MOD, value = Dist.CLIENT)
    public static class ClientModEvents
    {
        @SubscribeEvent
        public static void onClientSetup(FMLClientSetupEvent event)
        {
            // Some client setup code
            LOGGER.info("HELLO FROM CLIENT SETUP");
            LOGGER.info("MINECRAFT NAME >> {}", Minecraft.getInstance().getUser().getName());
        }
    }
}
