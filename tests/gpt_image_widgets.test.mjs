// Headless widget lifecycle regressions; run with node --test tests/gpt_image_widgets.test.mjs.
import assert from "node:assert/strict";
import { readFileSync } from "node:fs";
import test from "node:test";
import vm from "node:vm";

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
    const name = "KIE_GPTImage2_TextToImage";
    extension.beforeRegisterNodeDef(null, {
        name, input: { optional: { model: [Object.keys(rules), { kie_model_options: rules }] } },
    });
    const widgets = Object.entries({ aspect_ratio: "auto", resolution: "1K", model: "GPT Image 2", background: "opaque" })
        .map(([name, value]) => ({ name, value, options: {} }));
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
