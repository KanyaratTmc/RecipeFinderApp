from PyQt6.QtWidgets import (
    QApplication, QWidget, QPushButton, QVBoxLayout, QHBoxLayout, QLabel, QCheckBox, QFileDialog, QInputDialog, 
    QScrollArea, QGridLayout, QMessageBox
)
from PyQt6.QtGui import QPixmap
from PyQt6.QtCore import Qt
import sqlite3
import sys


# เชื่อมต่อฐานข้อมูล
con = sqlite3.connect('recipes.db')
cur = con.cursor()

# สร้างตาราง ingredients
cur.execute('''
CREATE TABLE IF NOT EXISTS ingredients (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL UNIQUE,
    image TEXT
)
''')

# สร้างตาราง recipes
cur.execute('''
CREATE TABLE IF NOT EXISTS recipes (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL UNIQUE,
    image TEXT
)
''')

# สร้างตาราง recipe_ingredient สำหรับเชื่อมโยงสูตรอาหารกับวัตถุดิบ
cur.execute('''
CREATE TABLE IF NOT EXISTS recipe_ingredient (
    recipe_id INTEGER,
    ingredient_id INTEGER,
    FOREIGN KEY (recipe_id) REFERENCES recipes(id),
    FOREIGN KEY (ingredient_id) REFERENCES ingredients(id),
    PRIMARY KEY (recipe_id, ingredient_id)
)
''')

con.commit()

class RecipeFinder(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Recipe Finder")
        self.setGeometry(450, 150, 800, 650)
        self.setStyleSheet("background-color: #f4f4f4;")
        self.UI()
        self.show()

    def UI(self):
        self.mainDesign()
        self.layouts()

    def mainDesign(self):
        self.ingredientGrid = QWidget()
        self.gridLayout = QGridLayout()
        self.loadIngredients()

        self.btnAddIngredient = QPushButton("Add Ingredient")
        self.btnAddIngredient.setStyleSheet("background-color: #90ee90; padding: 10px; font-size: 16px;")
        self.btnAddIngredient.clicked.connect(self.addIngredient)

        self.btnFindRecipes = QPushButton("Find Recipes")
        self.btnFindRecipes.setStyleSheet("background-color: #32cd32; padding: 10px; font-size: 16px;")
        self.btnFindRecipes.clicked.connect(self.findRecipes)

        self.btnAddRecipe = QPushButton("Add Recipe")
        self.btnAddRecipe.setStyleSheet("background-color: #87cefa; padding: 10px; font-size: 16px;")
        self.btnAddRecipe.clicked.connect(self.addRecipe)

        self.btnDeleteIngredient = QPushButton("Delete Ingredient")
        self.btnDeleteIngredient.setStyleSheet("background-color: #ff69b4; padding: 10px; font-size: 16px;")
        self.btnDeleteIngredient.clicked.connect(self.deleteIngredient)

    def layouts(self):
        self.mainLayout = QVBoxLayout()
        self.mainLayout.addWidget(self.ingredientGrid)
        self.mainLayout.addWidget(self.btnAddIngredient)
        self.mainLayout.addWidget(self.btnFindRecipes)
        self.mainLayout.addWidget(self.btnAddRecipe)
        self.mainLayout.addWidget(self.btnDeleteIngredient)
        self.setLayout(self.mainLayout)

    def loadIngredients(self):
        self.gridLayout.setContentsMargins(10, 10, 10, 10)
        self.gridLayout.setSpacing(10)

        # ลบวิดเจ็ตที่มีอยู่แล้ว
        for i in reversed(range(self.gridLayout.count())):
            widget = self.gridLayout.itemAt(i).widget()
            if widget is not None:
                widget.deleteLater()

        # ดึงข้อมูลจากฐานข้อมูลและเรียงตามชื่อ
        query = "SELECT id, name, image FROM ingredients ORDER BY name"
        ingredients = cur.execute(query).fetchall()

        row = 0
        col = 0
        for ingredient_id, name, image_path in ingredients:
            itemWidget = QWidget()
            itemLayout = QVBoxLayout()

            nameLabel = QLabel(name)
            nameLabel.setStyleSheet("font-size: 16px; font-weight: bold;")

            ingredientImage = QLabel()
            if image_path:
                pixmap = QPixmap(image_path)
                ingredientImage.setPixmap(pixmap.scaled(100, 100, Qt.AspectRatioMode.KeepAspectRatio))
            else:
                ingredientImage.setText("No Image")

            imageLayout = QHBoxLayout()
            imageLayout.addWidget(ingredientImage, alignment=Qt.AlignmentFlag.AlignCenter)

            checkbox = QCheckBox("Select")
            checkbox.setProperty("ingredient_id", ingredient_id)

            itemLayout.addLayout(imageLayout)
            itemLayout.addWidget(nameLabel)
            itemLayout.addWidget(checkbox)
            itemWidget.setLayout(itemLayout)
            itemWidget.setStyleSheet("background-color: #ffffff; padding: 10px; border-radius: 10px;")
            self.gridLayout.addWidget(itemWidget, row, col)

            col += 1
            if col == 3:
                col = 0
                row += 1

        scrollArea = QScrollArea()
        scrollArea.setWidgetResizable(True)
        scrollArea.setWidget(self.ingredientGrid)
        self.ingredientGrid.setLayout(self.gridLayout)
        self.ingredientGrid = scrollArea


    def addIngredient(self):
        text, ok = QInputDialog.getText(self, 'Add Ingredient', 'Enter ingredient name:')
        if ok and text:
            image_path = QFileDialog.getOpenFileName(self, 'Select Ingredient Image', '', 'Images (*.png *.jpg *.jpeg *.bmp)')[0]
            try:
                cur.execute("INSERT INTO ingredients (name, image) VALUES (?, ?)", (text, image_path))
                con.commit()
                self.loadIngredients()
                QMessageBox.information(self, "Success", "Ingredient added successfully.")
            except sqlite3.IntegrityError:
                QMessageBox.warning(self, "Error", "This ingredient already exists!")

    def addRecipe(self):
        recipe_name, ok = QInputDialog.getText(self, 'Add Recipe', 'Enter recipe name:')
        if ok and recipe_name:
            selected_ingredients = [widget.property("ingredient_id") for widget in self.findChildren(QCheckBox) if widget.isChecked()]

            if not selected_ingredients:
                QMessageBox.warning(self, "Warning", "Please select at least one ingredient!")
                return

            image_path = QFileDialog.getOpenFileName(self, 'Select Recipe Image', '', 'Images (*.png *.jpg *.jpeg *.bmp)')[0]
            cur.execute("INSERT INTO recipes (name, image) VALUES (?, ?)", (recipe_name, image_path))
            recipe_id = cur.lastrowid

            for ingredient_id in selected_ingredients:
                cur.execute("INSERT INTO recipe_ingredient (recipe_id, ingredient_id) VALUES (?, ?)", (recipe_id, ingredient_id))

            con.commit()
            QMessageBox.information(self, "Success", "Recipe added successfully.")

    def findRecipes(self):
        selected_ingredients = [widget.property("ingredient_id") for widget in self.findChildren(QCheckBox) if widget.isChecked()]

        if not selected_ingredients:
            QMessageBox.warning(self, "Warning", "Please select at least one ingredient!")
            return

        placeholders = ','.join('?' for _ in selected_ingredients)
        query = f'''
        SELECT r.name, r.image FROM recipes r
        JOIN recipe_ingredient ri ON r.id = ri.recipe_id
        WHERE ri.ingredient_id IN ({placeholders})
        GROUP BY r.id

        '''
        recipes = cur.execute(query, selected_ingredients).fetchall()
        self.displayRecipes(recipes)

    def displayRecipes(self, foundRecipes):
        print("Displaying Recipes:", foundRecipes)
        
        self.recipeWindow = QWidget()
        self.recipeWindow.setWindowTitle("Found Recipes")
        layout = QVBoxLayout()
        titleLabel = QLabel("Found Recipes")
        titleLabel.setStyleSheet("font-size: 24px; font-weight: bold; margin-bottom: 15px;")
        titleLabel.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(titleLabel)


        scrollArea = QScrollArea()
        containerWidget = QWidget()
        containerLayout = QVBoxLayout()

        for recipeName, image_path in foundRecipes:
            recipeCard = QWidget()
            recipeLayout = QVBoxLayout()

            nameLabel = QLabel(recipeName)
            nameLabel.setStyleSheet("font-size: 18px; font-weight: bold;")

            recipeImage = QLabel()
            if image_path:
                pixmap = QPixmap(image_path)
                recipeImage.setPixmap(pixmap.scaled(100, 100, Qt.AspectRatioMode.KeepAspectRatio))
            else:
                recipeImage.setText("No Image")

            recipeLayout.addWidget(recipeImage)
            recipeLayout.addWidget(nameLabel)

            recipeCard.setLayout(recipeLayout)
            containerLayout.addWidget(recipeCard)

        containerWidget.setLayout(containerLayout)
        scrollArea.setWidget(containerWidget)

        layout.addWidget(scrollArea)
        self.recipeWindow.setLayout(layout)
        self.recipeWindow.show()


    def deleteIngredient(self):
        selectedIngredients = [widget.property("ingredient_id") for widget in self.findChildren(QCheckBox) if widget.isChecked()]

        if not selectedIngredients:
            QMessageBox.warning(self, "Warning", "Please select at least one ingredient to delete!")
            return

        for ingredient_id in selectedIngredients:
            cur.execute("DELETE FROM ingredients WHERE id = ?", (ingredient_id,))
            cur.execute("DELETE FROM recipe_ingredient WHERE ingredient_id = ?", (ingredient_id,))

        con.commit()
        self.loadIngredients()
        QMessageBox.information(self, "Success", "Selected ingredient(s) deleted successfully.")


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = RecipeFinder()
    sys.exit(app.exec())
