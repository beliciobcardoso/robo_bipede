FREECAD_CMD ?= flatpak run --command=FreeCADCmd org.freecad.FreeCAD
BUILD_DIR   := cad/build
PARTS       := $(notdir $(basename $(wildcard cad/parts/*.py)))
MODELS      := $(PARTS:%=$(BUILD_DIR)/%.FCStd)

.PHONY: all clean $(PARTS)

all: $(MODELS)

# `make servo_sg90` builds a single part
$(PARTS): %: $(BUILD_DIR)/%.FCStd

# FreeCADCmd exits 0 even when the script raises, so failure is detected
# from its output and from the missing model file.
$(BUILD_DIR)/%.FCStd: cad/parts/%.py
	@rm -f $@
	@out=$$(CAD_OUT_DIR=$(BUILD_DIR) $(FREECAD_CMD) $< 2>&1); \
	if echo "$$out" | grep -q "Exception" || [ ! -f $@ ]; then \
		echo "$$out" >&2; echo "FAILED: $<" >&2; exit 1; \
	fi; \
	echo "$$out" | grep '^\['

clean:
	rm -rf $(BUILD_DIR)
