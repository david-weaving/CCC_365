

-- Creating all my tables:

CREATE TABLE cart(
    id INT AUTO_INCREMENT PRIMARY KEY,
    class TEXT NOT NULL DEFAULT 'class',
    `level` INT NOT NULL DEFAULT 0
);

CREATE TABLE cart_line_item(
    primary_key INT AUTO_INCREMENT PRIMARY KEY,
    cart_id INT,
    potion_id TEXT NOT NULL 'no pot',
    quantity INT NOT NULL DEFAULT 0,
    FOREIGN KEY (cart_id) REFERENCES cart(id)
);

CREATE TABLE gold_ledgers(
    id INT AUTO_INCREMENT PRIMARY KEY,
    gold INT NOT NULL DEFAULT 100
);

CREATE TABLE ml_ledgers(
    id INT AUTO_INCREMENT PRIMARY KEY,
    red_ml INT NOT NULL DEFAULT 0,
    green_ml INT NOT NULL DEFAULT 0,
    blue_ml INT NOT NULL DEFAULT 0,
    black_ml INT NOT NULL DEFAULT 0
);

CREATE TABLE potions(
    id INT AUTO_INCREMENT PRIMARY KEY,
    potion_name TEXT NOT NULL DEFAULT 'no pot',
    red_ml INT NOT NULL DEFAULT 0,
    green_ml INT NOT NULL DEFAULT 0,
    blue_ml INT NOT NULL DEFAULT 0,
    dark_ml INT NOT NULL DEFAULT 0,
    price INT NOT NULL DEFAULT 0
);

INSERT INTO potions (potion_name,red_ml, price) VALUES (red_potion, 100, 50);
INSERT INTO potions (potion_name,green_ml,price) VALUES (green_potion, 100, 50);
INSERT INTO potions (potion_name,blue_ml,price) VALUES (blue_potion, 100, 60);
INSERT INTO potions (potion_name,dark_ml,price) VALUES (dark_potion, 100, 50);
INSERT INTO potions (potion_name,red_ml,blue_ml,price) VALUES (purple_potion, 50,50,55);
INSERT INTO potions (potion_name,red_ml,green_ml,price) VALUES (yellow_potion, 50,50,50);
INSERT INTO potions (potion_name,red_ml,green_ml,blue_ml,price) VALUES (white_potion, 33,33,34,55);

CREATE TABLE potion_ledgers(
    id INT AUTO_INCREMENT PRIMARY KEY,
    potion_id INT,
    amount INT,
    FOREIGN KEY (potion_id) REFERENCES potions(id)
);

---------------------------------------------------------

-- Potion Inventory tracking:
SELECT potions.id, COALESCE(sum(potion_ledgers.amount),0) AS inventory, potions.red_ml AS red, potions.green_ml AS green, potions.blue_ml AS blue, potions.dark_ml AS dark,
potions.potion_name AS name
FROM potions
LEFT JOIN potion_ledgers ON potion_ledgers.potion_id = potions.id
GROUP BY potions.id
ORDER BY potions.id

---------------------------------------------------------

-- Total inventory
SELECT red_ml, green_ml, blue_ml, black_ml FROM ml_inventory;
SELECT gold FROM global_inventory;
SELECT SUM(inventory) AS total_inventory
FROM (
    SELECT COALESCE(SUM(potion_ledgers.amount), 0) AS inventory
    FROM potions
    LEFT JOIN potion_ledgers ON potion_ledgers.potion_id = potions.id
    GROUP BY potions.id
) AS inventory_table;

---------------------------------------------------------

-- admin.py, resetting:
UPDATE global_inventory SET gold = 100;
UPDATE ml_inventory SET red_ml = 0, green_ml = 0, blue_ml = 0, black_ml = 0;
DELETE FROM cart_line_item;
DELETE FROM cart;
DELETE FROM potion_ledgers;

---------------------------------------------------------

-- catalog
SELECT 
    potions.id, 
    COALESCE(SUM(potion_ledgers.amount), 0) AS inventory, 
    potions.red_ml AS red, 
    potions.green_ml AS green, 
    potions.blue_ml AS blue, 
    potions.dark_ml AS dark, 
    potions.potion_name AS name 
FROM 
    potions 
LEFT JOIN 
    potion_ledgers ON potion_ledgers.potion_id = potions.id 
GROUP BY 
    potions.id 
ORDER BY 
    potions.id;

---------------------------------------------------------

-- All other DB calls are used to select items or update them based on ml/potions/gold recieved/lost.

-- bottler

INSERT INTO potion_ledgers (potion_id, amount)
VALUES (potion ID, amount of that potion);

UPDATE ml_inventory
SET red_ml = red_ml - total_red,
    green_ml = green_ml - total_green,
    blue_ml = blue_ml - total_blue;

---------------------------------------------------------

-- barrels

UPDATE ml_inventory 
SET red_ml = red_ml + :red_ml, 
    green_ml = green_ml + :green_ml, 
    blue_ml = blue_ml + :blue_ml

UPDATE global_inventory
SET gold = gold - cost;



---------------------------------------------------------

-- cart id

INSERT INTO cart (class, level)
VALUES (:character_class, :level);
SELECT LAST_INSERT_ID() AS id;

---------------------------------------------------------

-- populating cart

INSERT INTO cart_line_item (primary_key, cart_id, potion_id, quantity)
VALUES (DEFAULT, :cart_id, :item_sku, :quantity);


---------------------------------------------------------

-- cart checkout



SELECT 
    cart_line_item.quantity, 
    potions.price, 
    potions.id 
FROM 
    cart_line_item 
JOIN 
    potions ON potions.potion_name = cart_line_item.potion_id 
WHERE 
    cart_line_item.cart_id = :cart_id;


INSERT INTO potion_ledgers (id, potion_id, amount) VALUES (DEFAULT, potion ID, -amount);

UPDATE global_inventory 
SET gold = gold + cost;


---------------------------------------------------------
