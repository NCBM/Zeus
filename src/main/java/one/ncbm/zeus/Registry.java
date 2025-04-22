package one.ncbm.zeus;

import net.minecraft.core.registries.Registries;
import net.minecraft.network.chat.Component;
import net.minecraft.resources.ResourceKey;
import net.minecraft.resources.ResourceLocation;
import net.minecraft.world.item.BlockItem;
import net.minecraft.world.item.CreativeModeTab;
import net.minecraft.world.item.CreativeModeTab.DisplayItemsGenerator;
import net.minecraft.world.item.Item;
import net.minecraft.world.level.block.Block;
import net.neoforged.neoforge.registries.DeferredBlock;
import net.neoforged.neoforge.registries.DeferredHolder;
import net.neoforged.neoforge.registries.DeferredItem;
import net.neoforged.neoforge.registries.DeferredRegister;

public class Registry {

    public static final DeferredRegister.Blocks BLOCKS = DeferredRegister.createBlocks(ZeusMain.MODID);
    public static final DeferredRegister.Items ITEMS = DeferredRegister.createItems(ZeusMain.MODID);
    public static final DeferredRegister<CreativeModeTab> CREATIVE_MODE_TABS = DeferredRegister.create(Registries.CREATIVE_MODE_TAB, ZeusMain.MODID);

    public static DeferredBlock<Block> block(String name) {
        return BLOCKS.registerSimpleBlock(name);
    }

    public static DeferredItem<BlockItem> blockItem(String name, DeferredBlock<Block> blockItem) {
        return ITEMS.registerSimpleBlockItem(name, blockItem);
    }

    public static DeferredItem<Item> item(String name) {
        return ITEMS.registerSimpleItem(name);
    }

    public static final DeferredHolder<CreativeModeTab, CreativeModeTab> creativeModeTab(
        String name, String langKey, DeferredItem<Item> iconItem, DisplayItemsGenerator itemSource
    ) {
        return CREATIVE_MODE_TABS.register(name, () -> CreativeModeTab.builder()
            .title(Component.translatable(langKey))
            .icon(() -> iconItem.get().getDefaultInstance())
            .displayItems(itemSource).build());
    }

    public static final DeferredHolder<CreativeModeTab, CreativeModeTab> creativeModeTabBefore(
        String name, String langKey, DeferredItem<Item> iconItem, DisplayItemsGenerator itemSource, ResourceLocation... before
    ) {
        return CREATIVE_MODE_TABS.register(name, () -> CreativeModeTab.builder()
            .title(Component.translatable(langKey))
            .withTabsBefore(before)
            .icon(() -> iconItem.get().getDefaultInstance())
            .displayItems(itemSource).build());
    }

    @SafeVarargs
    public static final DeferredHolder<CreativeModeTab, CreativeModeTab> creativeModeTabBefore(
        String name, String langKey, DeferredItem<Item> iconItem, DisplayItemsGenerator itemSource, ResourceKey<CreativeModeTab>... before
    ) {
        return CREATIVE_MODE_TABS.register(name, () -> CreativeModeTab.builder()
            .title(Component.translatable(langKey))
            .withTabsBefore(before)
            .icon(() -> iconItem.get().getDefaultInstance())
            .displayItems(itemSource).build());
    }

    public static final DeferredHolder<CreativeModeTab, CreativeModeTab> creativeModeTabAfter(
        String name, String langKey, DeferredItem<Item> iconItem, DisplayItemsGenerator itemSource, ResourceLocation... after
    ) {
        return CREATIVE_MODE_TABS.register(name, () -> CreativeModeTab.builder()
            .title(Component.translatable(langKey))
            .withTabsAfter(after)
            .icon(() -> iconItem.get().getDefaultInstance())
            .displayItems(itemSource).build());
    }

    @SafeVarargs
    public static final DeferredHolder<CreativeModeTab, CreativeModeTab> creativeModeTabAfter(
        String name, String langKey, DeferredItem<Item> iconItem, DisplayItemsGenerator itemSource, ResourceKey<CreativeModeTab>... after
    ) {
        return CREATIVE_MODE_TABS.register(name, () -> CreativeModeTab.builder()
            .title(Component.translatable(langKey))
            .withTabsAfter(after)
            .icon(() -> iconItem.get().getDefaultInstance())
            .displayItems(itemSource).build());
    }
}
