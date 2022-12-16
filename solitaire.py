WINDOW_SIZE = 840, 600

CARD_DIMENSIONS = QSize(80, 116)
CARD_RECT = QRect(0, 0, 80, 116)
CARD_SPACING_X = 110
CARD_BACK = QImage(os.path.join('images', 'back.png'))

DEAL_RECT = QRect(30, 30, 110, 140)

OFFSET_X = 50
OFFSET_Y = 50
WORK_STACK_Y = 200

SIDE_FACE = 0
SIDE_BACK = 1

BOUNCE_ENERGY = 0.8

# We store cards as numbers 1-13, since we only need
# to know their order for solitaire.
SUITS = ["C", "S", "H", "D"]


class Signals(QObject):
    complete = pyqtSignal()
    clicked = pyqtSignal()
    doubleclicked = pyqtSignal()


class Card(QGraphicsPixmapItem):

    def __init__(self, value, suit, *args, **kwargs):
        super(Card, self).__init__(*args, **kwargs)

        self.signals = Signals()

        self.stack = None  # Stack this card currently is in.
        self.child = None  # Card stacked on this one (for work deck).

        # Store the value & suit of the cards internal to it.
        self.value = value
        self.suit = suit
        self.side = None

        # For end animation only.
        self.vector = None

        # Cards have no internal transparent areas, so we can use this faster method.
        self.setShapeMode(QGraphicsPixmapItem.BoundingRectShape)
        self.setFlag(QGraphicsItem.ItemIsMovable)
        self.setFlag(QGraphicsItem.ItemSendsGeometryChanges)

        self.load_images()

    def load_images(self):
        self.face = QPixmap(
            os.path.join('cards', '%s%s.png' % (self.value, self.suit))
        )

        self.back = QPixmap(
            os.path.join('images', 'back.png')
        )

    def turn_face_up(self):
        self.side = SIDE_FACE
        self.setPixmap(self.face)

    def turn_back_up(self):
        self.side = SIDE_BACK
        self.setPixmap(self.back)

    @property
    def is_face_up(self):
        return self.side == SIDE_FACE

    @property
    def color(self):
        return 'r' if self.suit in ('H', 'D') else 'b'

    def mousePressEvent(self, e):
        if not self.is_face_up and self.stack.cards[-1] == self:
            self.turn_face_up()  # We can do this without checking.
            e.accept()
            return

        if self.stack and not self.stack.is_free_card(self):
            e.ignore()
            return

        self.stack.activate()

        e.accept()

        super(Card, self).mouseReleaseEvent(e)

    def mouseReleaseEvent(self, e):
        self.stack.deactivate()

        items = self.collidingItems()
        if items:
            # Find the topmost item from a different stack:
            for item in items:
                if ((isinstance(item, Card) and item.stack != self.stack) or
                    (isinstance(item, StackBase) and item != self.stack)):

                    if item.stack.is_valid_drop(self):
                        # Remove card + all children from previous stack, add to the new.
                        # Note: the only place there will be children is on a workstack.
                        cards = self.stack.remove_card(self)
                        item.stack.add_cards(cards)
                        break

        # Refresh this card's stack, pulling it back if it was dropped.
        self.stack.update()

        super(Card, self).mouseReleaseEvent(e)

    def mouseDoubleClickEvent(self, e):
        if self.stack.is_free_card(self):
            self.signals.doubleclicked.emit()
            e.accept()

        super(Card, self).mouseDoubleClickEvent(e)


class StackBase(QGraphicsRectItem):

    def __init__(self, *args, **kwargs):
        super(StackBase, self).__init__(*args, **kwargs)

        self.setRect(QRectF(CARD_RECT))
        self.setZValue(-1)

        # Cards on this deck, in order.
        self.cards = []

        # Store a self ref, so the collision logic can handle cards and
        # stacks with the same approach.
        self.stack = self
        self.setup()
        self.reset()

    def setup(self):
        pass

    def reset(self):
        self.remove_all_cards()

    def update(self):
        for n, card in enumerate(self.cards):
            card.setPos( self.pos() + QPointF(n * self.offset_x, n * self.offset_y))
            card.setZValue(n)

    def activate(self):
        pass

    def deactivate(self):
        pass

    def add_card(self, card, update=True):
        card.stack = self
        self.cards.append(card)
        if update:
            self.update()

    def add_cards(self, cards):
        for card in cards:
            self.add_card(card, update=False)
        self.update()

    def remove_card(self, card):
        card.stack = None
        self.cards.remove(card)
        self.update()
        return [card] # Returns a list, as WorkStack must return children

    def remove_all_cards(self):
        for card in self.cards[:]:
            card.stack = None
        self.cards = []

    def is_valid_drop(self, card):
        return True

    def is_free_card(self, card):
        return False
