FREECAD_CMD ?= flatpak run --command=FreeCADCmd org.freecad.FreeCAD
BUILD_DIR   := cad/build
PARTS       := $(notdir $(basename $(wildcard cad/parts/*.py)))
MODELS      := $(PARTS:%=$(BUILD_DIR)/%.FCStd)

.PHONY: all clean preview $(PARTS)

all: $(MODELS)

# `make servo_sg90` builds a single part
$(PARTS): %: $(BUILD_DIR)/%.FCStd

# FreeCADCmd exits 0 even when the script raises, so failure is detected
# from its output and from the missing model file.
$(BUILD_DIR)/%.FCStd: cad/parts/%.py cad/cadlib.py
	@rm -f $@
	@out=$$(CAD_OUT_DIR=$(BUILD_DIR) $(FREECAD_CMD) $< 2>&1); \
	if echo "$$out" | grep -q "Exception" || [ ! -f $@ ]; then \
		echo "$$out" >&2; echo "FAILED: $<" >&2; exit 1; \
	fi; \
	echo "$$out" | grep '^\['

# 3D preview of the whole robot from the current design (docs/previa.md): servo and bearing
# meshes from their CAD scripts, robot from sim/tools/build_biped.py, images rendered by MuJoCo.
MESHES := sim/models/meshes
preview: $(BUILD_DIR)/servo_sg90.FCStd $(BUILD_DIR)/bearing_623zz.FCStd
	@mkdir -p $(MESHES)
	@for spec in servo_sg90:ServoSG90 bearing_623zz:Bearing623ZZ; do \
		n=$${spec%%:*}; o=$${spec##*:}; \
		flatpak run --env=SRC=$(CURDIR)/$(BUILD_DIR)/$$n.FCStd --env=OBJ=$$o --env=OUT=$(CURDIR)/$(MESHES)/$$n.stl \
			--command=FreeCADCmd org.freecad.FreeCAD tools/export_stl.py 2>&1 | grep '^\[export' || exit 1; \
	done
	@.venv/bin/python sim/tools/build_biped.py --preview
	@MUJOCO_GL=glfw .venv/bin/python sim/tools/render_preview.py

# Parts that import another part's DIMS rebuild when that part changes
$(BUILD_DIR)/snap_socket.FCStd: cad/parts/snap_clip.py

clean:
	rm -rf $(BUILD_DIR)
