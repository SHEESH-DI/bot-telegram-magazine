CREATE TABLE IF NOT EXISTS product (
    id bigint GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    name varchar(200) NOT NULL CHECK (length(trim(name)) > 0),
    image_key text NOT NULL UNIQUE,
    telegram_chat_id bigint,
    telegram_message_id bigint,
    created_at timestamptz NOT NULL DEFAULT now(),
    UNIQUE (telegram_chat_id, telegram_message_id)
);

CREATE TABLE IF NOT EXISTS customer_session (
    id uuid PRIMARY KEY,
    created_at timestamptz NOT NULL DEFAULT now(),
    expires_at timestamptz NOT NULL DEFAULT now() + interval '30 days'
);

CREATE TABLE IF NOT EXISTS cart_item (
    session_id uuid NOT NULL REFERENCES customer_session(id),
    product_id bigint NOT NULL REFERENCES product(id),
    quantity integer NOT NULL CHECK (quantity BETWEEN 1 AND 99),
    PRIMARY KEY (session_id, product_id)
);

CREATE TABLE IF NOT EXISTS customer_order (
    id uuid PRIMARY KEY,
    session_id uuid NOT NULL REFERENCES customer_session(id),
    request_id uuid NOT NULL,
    name varchar(200) NOT NULL,
    contact varchar(300) NOT NULL,
    created_at timestamptz NOT NULL DEFAULT now(),
    UNIQUE (session_id, request_id)
);

CREATE TABLE IF NOT EXISTS order_item (
    order_id uuid NOT NULL REFERENCES customer_order(id),
    product_id bigint NOT NULL REFERENCES product(id),
    name varchar(200) NOT NULL,
    quantity integer NOT NULL CHECK (quantity > 0),
    PRIMARY KEY (order_id, product_id)
);

CREATE TABLE IF NOT EXISTS telegram_update (
    update_id bigint PRIMARY KEY,
    processed_at timestamptz NOT NULL DEFAULT now()
);
