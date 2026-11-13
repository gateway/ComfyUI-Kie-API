// Headless widget lifecycle regressions; run with node --test tests/gpt_image_widgets.test.mjs.
import assert from "node:assert/strict";
import { readFileSync } from "node:fs";
import test from "node:test";
import vm from "node:vm";

test("legacy extension never intercepts native DynamicCombo nodes", () => {
    let extension;
    vm.runInNewContext(source, {
        app: { registerExtension(value) { extension = value; } }, queueMicrotask,
    });
    for (const name of ["KIE_GPTImage_TextToImage", "KIE_GPTImage_ImageToImage"]) {
        extension.beforeRegisterNodeDef(null, {name, input: {required: {}}});
        const callback = () => {};
        const node = {comfyClass: name, widgets: [{name: "model", value: "test", callback}]};
        extension.nodeCreated(node);
        extension.loadedGraphNode(node);
        assert.equal(node.widgets[0].callback, callback);
        assert.equal(node.onConfigure, undefined);
    }
});

const source = readFileSync(new URL("../js/gpt_image.js", import.meta.url), "utf8")
    .replace('import { app } from "../../scripts/app.js";', "");

function fixture() {
    let extension;
    vm.runInNewContext(source, {
        app: { registerExtension(value) { extension = value; } }, queueMicrotask,
    });
    const rules = {
        "GPT Image 2": {
            aspect_ratios: ["auto", "1:1"],
            resolutions: { auto: ["1K"], "1:1": ["1K", "2K"] },
            backgrounds: ["opaque"],
        },
        "GPT Image 2.5 Flare": {
            aspect_ratios: ["auto", "1:1", "27:16"],
            resolutions: { auto: ["1K", "2K", "4K"], "1:1": ["1K", "2K", "4K"], "27:16": ["1K"] },
            backgrounds: ["opaque", "transparent", "auto"],
        },
    };
    rules["GPT Image 2.6 Flare"] = {
        aspect_ratios: ["auto", "5:4"], resolutions: {auto: ["1K", "2K", "4K"], "5:4": ["1K", "2K", "4K"]},
        backgrounds: ["opaque", "transparent", "auto"], formats: ["png", "jpeg", "webp", "gif", "svg"],
        advanced: true, frame_counts: ["2", "9", "16"],
    };
    rules["GPT Image 2.6 Economy"] = {
        aspect_ratios: ["auto", "1:1"], resolutions: {auto: ["1K"], "1:1": ["1K"]},
        backgrounds: ["opaque", "transparent", "auto"], formats: ["png", "gif"],
        advanced: false, economy: true, frame_counts: ["auto", "4", "9", "16", "64"],
    };
    const name = "KIE_GPTImage2_TextToImage";
    extension.beforeRegisterNodeDef(null, {
        name, input: { optional: { model: [Object.keys(rules), { kie_model_options: rules }] } },
    });
    const widgets = Object.entries({ aspect_ratio: "auto", resolution: "1K", model: "GPT Image 2", background: "opaque", output_format: "png", quality: "medium", complexity: "high", moderation: "low", output_compression: 100, frame_count: "9", frame_duration_ms: 200, gif_size: "auto", svg_model: "gpt-5.6-luna" })
        .map(([name, value]) => ({ name, value, options: {}, type: "combo" }));
    let configured = false;
    const node = { comfyClass: name, widgets, inputs: [], onConfigure() { configured = true; } };
    extension.nodeCreated(node);
    const get = (name) => widgets.find((widget) => widget.name === name);
    return { node, get, configured: () => configured };
}

test("cloned 2.5 values refresh menus without normalizing saved values", () => {
    const { node, get, configured } = fixture();
    get("model").value = "GPT Image 2.5 Flare";
    get("resolution").value = "4K";
    get("background").value = "transparent";
    node.onConfigure({});
    assert.equal(configured(), true);
    assert.ok(get("resolution").options.values.includes("4K"));
    assert.ok(get("background").options.values.includes("transparent"));
    assert.equal(get("resolution").value, "4K");
    assert.equal(get("background").value, "transparent");
});

test("connected selectors restore all potentially valid choices", async () => {
    for (const input of ["model", "aspect_ratio"]) {
        const { node, get } = fixture();
        if (input === "aspect_ratio") {
            get("model").value = "GPT Image 2.5 Flare";
            get("aspect_ratio").value = "27:16";
            node.onConfigure({});
        }
        assert.equal(get("resolution").options.values.length, 1);
        node.inputs.push({ name: input, link: 1 });
        node.onConnectionsChange();
        await new Promise(queueMicrotask);
        assert.ok(get("resolution").options.values.includes("4K"));
        node.inputs[0].link = null;
        node.onConnectionsChange();
        await new Promise(queueMicrotask);
        assert.equal(get("resolution").options.values.length, 1);
    }
});

test("explicit model changes normalize incompatible selections", () => {
    const { node, get } = fixture();
    get("model").value = "GPT Image 2.5 Flare";
    get("aspect_ratio").value = "27:16";
    get("background").value = "transparent";
    node.onConfigure({});
    get("model").value = "GPT Image 2";
    get("model").callback("GPT Image 2");
    assert.equal(get("aspect_ratio").value, "auto");
    assert.equal(get("background").value, "opaque");
});


test("2.6 format controls follow model and output choices", () => {
    const { node, get } = fixture();
    get("model").value = "GPT Image 2.6 Flare";
    get("model").callback();
    assert.equal(get("quality").type, "combo");
    assert.equal(get("frame_count").type, "hidden");
    get("output_format").value = "gif";
    get("output_format").callback();
    assert.equal(get("frame_count").type, "combo");
    assert.equal(get("gif_size").type, "combo");
    assert.equal(get("svg_model").type, "hidden");
    get("model").value = "GPT Image 2.6 Economy";
    get("model").callback();
    assert.equal(get("quality").type, "hidden");
    assert.equal(get("gif_size").type, "hidden");
    assert.ok(get("frame_count").options.values.includes("64"));
    get("model").value = "GPT Image 2";
    get("model").callback();
    assert.equal(get("output_format").value, "png");
});

test("connected output format exposes all applicable controls", async () => {
    const { node, get } = fixture();
    get("model").value = "GPT Image 2.6 Flare";
    get("model").callback();
    node.inputs.push({name: "output_format", link: 1});
    node.onConnectionsChange();
    await new Promise(queueMicrotask);
    assert.equal(get("frame_count").type, "combo");
    assert.equal(get("svg_model").type, "combo");
    assert.equal(get("output_compression").type, "combo");
});
