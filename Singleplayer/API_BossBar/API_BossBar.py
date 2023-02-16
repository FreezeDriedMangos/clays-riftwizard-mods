import mods.API_Universal.APIs.API_DrawLevel.API_DrawLevel as API_DrawLevel
import pygame

####################################################
# Importing RiftWizard.py                          |
# Credit to trung on discord                       |
#                                                  |
#----------------------------------------------    |
import inspect #                                   |
def get_RiftWizard(): #                            |
    # Returns the RiftWizard.py module object      |
    for f in inspect.stack()[::-1]: #              |
        if "file 'RiftWizard.py'" in str(f): #     |
            return inspect.getmodule(f[0]) #       |
	 #                                             |
    return inspect.getmodule(f[0]) #               |
#                                                  |
RiftWizard = get_RiftWizard() #                    |
#                                                  |
#                                                  |
####################################################

_boss_bar = None
_boss_bar_frame = RiftWizard.get_image(["API_BossBar", "frame"])
boss_bar_percent = 1
draw_boss_bar = False

class BossBarLayer(API_DrawLevel.Layer):
	def __init__(self):
		super().__init__(999999)
		self.units: List[Level.Unit] = []
		
	## Called when the layer should be drawn
	def draw_layer(self):
		global draw_boss_bar
		global _boss_bar

		if not _boss_bar:
			_boss_bar = pygame.Surface((400+25*2, 10+10*2)).convert_alpha()

		_boss_bar.fill((0, 0, 0, 0))
		pygame.draw.rect(_boss_bar, (255, 0, 0), pygame.Rect(25, 5, boss_bar_percent*400, 21))
		_boss_bar.set_alpha(100)
		self.level_display.blit(_boss_bar, (0, 0))

		_boss_bar.fill((0, 0, 0, 0))
		_boss_bar.blit(_boss_bar_frame, (0, 0))
		_boss_bar.set_alpha(200)
		self.level_display.blit(_boss_bar, (0, 0))

	def should_draw(self):
		global draw_boss_bar
		return draw_boss_bar

API_DrawLevel.layers.append(BossBarLayer())

