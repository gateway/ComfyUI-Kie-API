import { app } from "../../scripts/app.js";

const nodeNames = new Set(["KIE_GPTImage2_TextToImage", "KIE_GPTImage2_ImageToImage"]);
const definitions = new Map();

function syncOptions(node, normalize = false) {
    const rules = definitions.get(node.comfyClass);
    if (!rules) return;
    const widgets = Object.fromEntries((node.widgets ?? []).map((widget) => [widget.name, widget]));
    const isLinked = (name) => node.inputs?.some((input) => input.name === name && input.link != null);
    // A connected selector is unknown until execution: offer the union of valid choices.
    const candidates = isLinked("model") ? Object.values(rules) : [rules[widgets.model?.value]];
    if (candidates.some((options) => !options)) return;
    const union = (values) => [...new Set(values.flat())];
    const update = (name, values) => {
        const widget = widgets[name];
        if (!widget || !values || isLinked(name)) return;
        widget.options.values = [...values];
        if (normalize && !values.includes(widget.value)) {
            widget.value = values[0];
            widget.callback?.(widget.value);
        }
    };
    update("aspect_ratio", union(candidates.map((options) => options.aspect_ratios)));
    const resolutions = union(candidates.flatMap((options) => isLinked("aspect_ratio")
        ? Object.values(options.resolutions)
        : [options.resolutions[widgets.aspect_ratio?.value] ?? []]));
    if (resolutions.length) update("resolution", resolutions);
    update("background", union(candidates.map((options) => options.backgrounds)));
    update("output_format", union(candidates.map((options) => options.formats ?? ["png"])));
    update("frame_count", union(candidates.map((options) => options.frame_counts ?? ["9"])));
    const formats = isLinked("output_format")
        ? union(candidates.map((options) => options.formats ?? ["png"]))
        : [widgets.output_format?.value ?? "png"];
    const advanced = candidates.some((options) => options.advanced);
    const gif = formats.includes("gif");
    const visible = {
        quality: advanced, complexity: advanced, moderation: advanced,
        output_compression: advanced && formats.some((format) => ["jpeg", "webp"].includes(format)),
        svg_model: advanced && formats.includes("svg"),
        frame_count: gif, frame_duration_ms: gif,
        gif_size: gif && advanced && node.comfyClass === "KIE_GPTImage2_TextToImage",
    };
    for (const [name, show] of Object.entries(visible)) {
        const widget = widgets[name];
        if (!widget || isLinked(name)) continue;
        widget.kieOriginal ??= { type: widget.type, computeSize: widget.computeSize };
        widget.type = show ? widget.kieOriginal.type : "hidden";
        widget.computeSize = show ? widget.kieOriginal.computeSize : () => [0, -4];
    }
    node.setDirtyCanvas?.(true, true);
}

app.registerExtension({
    name: "KIE.GPTImageOptions",
    beforeRegisterNodeDef(_nodeType, nodeData) {
        if (nodeNames.has(nodeData.name)) {
            definitions.set(nodeData.name, nodeData.input.optional.model[1].kie_model_options);
        }
    },
    nodeCreated(node) {
        if (!nodeNames.has(node.comfyClass)) return;
        const onConfigure = node.onConfigure;
        node.onConfigure = function (...args) {
            const result = onConfigure?.apply(this, args);
            // Covers clone/paste as well as full graph loading, without rewriting values.
            syncOptions(this);
            return result;
        };
        const onConnectionsChange = node.onConnectionsChange;
        node.onConnectionsChange = function (...args) {
            const result = onConnectionsChange?.apply(this, args);
            // Wait for connection bookkeeping to finish before reading link state.
            queueMicrotask(() => syncOptions(this));
            return result;
        };
        for (const widget of node.widgets ?? []) {
            if (!["model", "aspect_ratio", "output_format"].includes(widget.name)) continue;
            const original = widget.callback;
            widget.callback = function (...args) {
                const result = original?.apply(this, args);
                syncOptions(node, true);
                return result;
            };
        }
        syncOptions(node);
    },
    loadedGraphNode(node) {
        // Never silently rewrite a saved workflow's parameters on load.
        syncOptions(node);
    },
});
