ALTER TABLE product ADD COLUMN IF NOT EXISTS price_kopecks integer NOT NULL DEFAULT 49900 CHECK (price_kopecks > 0);
ALTER TABLE order_item ADD COLUMN IF NOT EXISTS price_kopecks integer NOT NULL DEFAULT 0 CHECK (price_kopecks >= 0);

UPDATE product SET price_kopecks = 49900 WHERE image_key = 'demo/cup.jpg';
UPDATE product SET price_kopecks = 29900 WHERE image_key = 'demo/notebook.jpg';
